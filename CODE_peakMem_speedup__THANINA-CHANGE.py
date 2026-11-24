from pathlib import Path
import argparse
import warnings

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, LogLocator, ScalarFormatter

MARKER_ORDER = ['CDS', 'INT', 'IGS']
LINESTYLE_BY_MARKER = {'CDS': 'solid', 'INT': 'dashed', 'IGS': 'dotted'}
DATASET_ORDER = [
    'benchmark_ZhangNNEtAl2025_53angiosperms',
    'benchmark_YangEtAl2022_Asteraceae',
    'benchmark_YangEtAl2022_monocots',
    'benchmark_YangEtAl2022_angiosperms',
    'benchmark_ZhangNNEtAl2025_13724angiosperms',
]
DATASET_COLORS = dict(zip(DATASET_ORDER, ['#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#e41a1c']))
DATASET_LABELS = dict(zip(DATASET_ORDER, ['Angiosperms (n=53)', 'Asteraceae (n=155)', 'Monocot (n=733)', 'Angiosperms (n=2,585)', 'Angiosperms (n=13,724)']))


def parse_args():
    parser = argparse.ArgumentParser(description='Create combined speedup and memory scaling figures.')
    parser.add_argument('input_csv', nargs='?', default='results.csv')
    parser.add_argument('output_path_stem', nargs='?', default='Vis/factors_across_datasets')
    return parser.parse_args()


def elapsed_to_seconds(value):
    parts = str(value).strip().split(':')
    if len(parts) not in (2, 3):
        raise ValueError(f'Invalid elapsed time: {value!r}')
    total = 0.0
    for part in parts:
        total = total * 60 + float(part)
    if not 0 < total < float('inf'):
        raise ValueError(f'Invalid elapsed time: {value!r}')
    return total


def load_data(path):
    df = pd.read_csv(path, dtype={'Elapsed': str})
    required = {'dataset', 'threads', 'mode', 'Elapsed', 'MaxRSS_KB'}
    if missing := required - set(df.columns):
        raise ValueError(f'Missing CSV columns: {sorted(missing)}')
    df['marker'] = df['mode'].astype(str).str.strip().str.upper()
    df['dataset'] = df['dataset'].astype(str).str.strip()
    df = df[df['marker'].isin(MARKER_ORDER) & df['dataset'].isin(DATASET_ORDER)].copy()
    if df.empty:
        raise ValueError('No recognized dataset/marker combinations in CSV.')
    df['threads'] = pd.to_numeric(df['threads'], errors='raise')
    if not (df['threads'].notna() & (df['threads'] > 0) & (df['threads'] % 1 == 0)).all():
        raise ValueError('Thread counts must be positive integers.')
    df['threads'] = df['threads'].astype(int)
    df['elapsed_seconds'] = df['Elapsed'].apply(elapsed_to_seconds)
    # GNU time reports peak RSS in KiB on Linux. Convert to decimal GB.
    df['max_ram_gb'] = pd.to_numeric(df['MaxRSS_KB'], errors='raise') * 1024 / 1e9
    if not (df['max_ram_gb'].notna() & (df['max_ram_gb'] > 0) & (df['max_ram_gb'] < float('inf'))).all():
        raise ValueError('MaxRSS_KB must be positive and finite for logarithmic plotting.')
    return df


def build_speedup_df(df):
    rows = []
    for (dataset, marker), grp in df.groupby(['dataset', 'marker']):
        baseline_series = grp.loc[grp['threads'] == 1, 'elapsed_seconds']
        if baseline_series.empty:
            warnings.warn(f'No one-thread baseline for {dataset} / {marker}; omitted from speedup panel.')
            continue
        baseline = baseline_series.iloc[0]
        for _, row in grp.sort_values('threads').iterrows():
            speedup = baseline / row['elapsed_seconds']
            rows.append(dict(dataset=dataset, marker=marker, threads=row['threads'], speedup=speedup, speedup_percent=(speedup - 1) * 100))
    return pd.DataFrame(rows, columns=['dataset', 'marker', 'threads', 'speedup', 'speedup_percent'])


def apply_common_axes_style(ax, threads):
    max_threads = max(threads)
    ticks = sorted(set([x for x in [1, 2, 4, 8, 16, 32] if x <= max_threads] + list(threads)))
    ax.set_xscale('log', base=2)
    ax.set_xticks(ticks)
    ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.grid(True, which='major', alpha=0.3)
    ax.set_xlabel('Number of threads (log2 scale)')


def add_horizontal_top_legends(fig, datasets):
    dataset_handles = [Line2D([], [], linestyle='None', label='DATASET')]
    dataset_handles += [Line2D([0], [0], color=DATASET_COLORS[d], lw=2.8, marker='o', markersize=6, label=DATASET_LABELS[d]) for d in datasets]
    marker_handles = [Line2D([], [], linestyle='None', label='MARKER')]
    marker_handles += [Line2D([0], [0], color='black', lw=2.8, linestyle=LINESTYLE_BY_MARKER[m], label=m) for m in MARKER_ORDER]
    legend = fig.legend(handles=dataset_handles, loc='upper center', bbox_to_anchor=(0.5, 0.985), ncol=len(dataset_handles), columnspacing=0.9, handletextpad=0.5, labelspacing=0.4, handlelength=2.6, frameon=False)
    fig.add_artist(legend)
    fig.legend(handles=marker_handles, loc='upper center', bbox_to_anchor=(0.5, 0.935), ncol=4, columnspacing=0.9, handletextpad=0.5, labelspacing=0.4, handlelength=2.6, frameon=False)


def plot_panel(ax, plot_df, value_col, y_label, title, threads, is_memory_panel=False):
    for dataset in DATASET_ORDER:
        for marker in MARKER_ORDER:
            sub = plot_df[(plot_df['dataset'] == dataset) & (plot_df['marker'] == marker)].sort_values('threads')
            if sub.empty:
                continue
            ax.plot(sub['threads'], sub[value_col], color=DATASET_COLORS[dataset], linestyle=LINESTYLE_BY_MARKER[marker], linewidth=2.2, marker='o', markersize=5)
    apply_common_axes_style(ax, threads)
    if is_memory_panel:
        ax.set_yscale('log', base=10)
        ax.yaxis.set_major_locator(LogLocator(base=10.0, subs=(1.0,)))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f'{value:g}'))
    else:
        ax.set_yscale('linear')
        if plot_df.empty:
            ax.text(0.5, 0.5, 'No one-thread baselines available', transform=ax.transAxes, ha='center')
    ax.set_ylabel(y_label)
    ax.set_title(title)


def plot_side_by_side(speedup_df, memory_df, output_stem):
    datasets = [d for d in DATASET_ORDER if d in set(memory_df['dataset'])]
    threads = sorted(memory_df['threads'].unique())
    fig, axes = plt.subplots(1, 2, figsize=(15, 7.5))
    plot_panel(axes[0], speedup_df, 'speedup_percent', 'Speedup (%)', 'Speed Improvements Through Parallelization', threads)
    plot_panel(axes[1], memory_df, 'max_ram_gb', 'Peak RAM (GB)', 'Memory Scaling Across Datasets', threads, is_memory_panel=True)
    for ax, label in zip(axes, ['A', 'B']):
        ax.text(-0.07, 1.06, label, transform=ax.transAxes, fontsize=22, fontweight='bold', va='top', ha='left')
    add_horizontal_top_legends(fig, datasets)
    fig.subplots_adjust(left=0.055, right=0.985, top=0.80, bottom=0.11, wspace=0.14)
    fig.savefig(output_stem.with_name(f'{output_stem.name}.png'), dpi=300)
    fig.savefig(output_stem.with_name(f'{output_stem.name}.svg'))
    plt.close(fig)


def main():
    args = parse_args()
    output_stem = Path(args.output_path_stem)
    output_stem.parent.mkdir(parents=True, exist_ok=True)
    df = load_data(Path(args.input_csv))
    if df.duplicated(['dataset', 'marker', 'threads']).any():
        warnings.warn('Repeated runs detected; plotting all records and using the first one-thread record as baseline, as in the original script.')
    plot_side_by_side(build_speedup_df(df), df, output_stem)


if __name__ == '__main__':
    main()
