from pathlib import Path
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

try:
    from adjustText import adjust_text
except ImportError:
    adjust_text = None

MARKER_ORDER = ['CDS', 'INT', 'IGS']
LINESTYLE_BY_MARKER = {'CDS': 'solid', 'INT': 'dashed', 'IGS': 'dotted'}
DATASET_ORDER = [
    'benchmark_ZhangNNEtAl2025_53angiosperms',
    'benchmark_YangEtAl2022_Asteraceae',
    'benchmark_YangEtAl2022_monocots',
    'benchmark_YangEtAl2022_angiosperms',
    'benchmark_ZhangNNEtAl2025_13724angiosperms',
]
DATASET_LABELS = dict(zip(DATASET_ORDER, [
    'Angiosperms (n=53)', 'Asteraceae (n=155)', 'Monocot (n=733)',
    'Angiosperms (n=2,585)', 'Angiosperms (n=13,724)']))
DATASET_COLORS = dict(zip(DATASET_ORDER, ['#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#e41a1c']))


def parse_args():
    parser = argparse.ArgumentParser(description='Plot computation time from benchmark CSV data.')
    parser.add_argument('input_csv', nargs='?', default='results.csv')
    parser.add_argument('output_path_stem', nargs='?', default='./VIZ_SpeedImprovements/PlastomeBurst_SpeedImprovements_AllMarkers')
    return parser.parse_args()


def elapsed_to_minutes(value):
    """Convert GNU time m:ss or h:mm:ss to minutes for plotting only."""
    parts = str(value).strip().split(':')
    if len(parts) not in (2, 3):
        raise ValueError(f'Invalid elapsed time: {value!r}')
    try:
        numbers = [float(p) for p in parts]
    except ValueError as exc:
        raise ValueError(f'Invalid elapsed time: {value!r}') from exc
    if not all(np.isfinite(n) and n >= 0 for n in numbers) or numbers[-1] >= 60 or any(not n.is_integer() for n in numbers[:-1]) or (len(numbers) == 3 and numbers[1] >= 60):
        raise ValueError(f'Invalid elapsed time: {value!r}')
    return sum(n * 60**i for i, n in enumerate(reversed(numbers))) / 60.0


def format_duration_label(x_min):
    if pd.isna(x_min):
        return ''
    if x_min < 1:
        return f'{int(round(x_min * 60))} sec'
    if x_min >= 60:
        hours, minutes = divmod(int(round(x_min)), 60)
        return f'{hours} h {minutes} min' if minutes else f'{hours} h'
    return f'{x_min:.1f}'.removesuffix('.0') + ' min'


def compute_breaks(max_cpus, max_time_min):
    x_breaks = sorted({2**i for i in range(int(np.ceil(np.log2(max_cpus))) + 1) if 2**i <= max_cpus} | {max_cpus})
    y_breaks = [0, 0.5, 1, 5, 10, 20, 40, 60, 120, 240]
    while y_breaks[-1] < max_time_min:
        y_breaks.append(y_breaks[-1] * 2)
    return x_breaks, [v for v in y_breaks if v <= max_time_min]


def add_horizontal_top_legends(fig, datasets):
    dataset_handles = [Line2D([], [], linestyle='None', label='DATASET')] + [
        Line2D([0], [0], color=DATASET_COLORS[d], lw=2.8, marker='o', markersize=6, label=DATASET_LABELS[d]) for d in datasets]
    marker_handles = [Line2D([], [], linestyle='None', label='MARKER')] + [
        Line2D([0], [0], color='black', lw=2.8, linestyle=LINESTYLE_BY_MARKER[m], label=m) for m in MARKER_ORDER]
    options = dict(loc='upper center', columnspacing=0.9, handletextpad=0.5, labelspacing=0.4, handlelength=2.6, frameon=False)
    legend = fig.legend(handles=dataset_handles, bbox_to_anchor=(0.5, 0.985), ncol=len(dataset_handles), **options)
    fig.add_artist(legend)
    fig.legend(handles=marker_handles, bbox_to_anchor=(0.5, 0.955), ncol=4, **options)


def main():
    args = parse_args()
    input_csv = Path(args.input_csv)
    output_stem = Path(args.output_path_stem)
    output_stem.parent.mkdir(parents=True, exist_ok=True)
    plot_df = pd.read_csv(input_csv, dtype={'Elapsed': str})
    required = {'dataset', 'threads', 'mode', 'Elapsed'}
    missing = required - set(plot_df.columns)
    if missing:
        raise ValueError(f'Missing CSV columns: {sorted(missing)}')
    plot_df = plot_df.rename(columns={'dataset': 'DATASET', 'threads': 'CPUS', 'mode': 'MARKER'})
    plot_df['MARKER'] = plot_df['MARKER'].astype(str).str.strip().str.upper()
    plot_df = plot_df[plot_df['MARKER'].isin(MARKER_ORDER) & plot_df['DATASET'].isin(DATASET_ORDER)].copy()
    if plot_df.empty:
        raise ValueError('No rows match the configured datasets and markers.')
    plot_df['TIME_MIN'] = plot_df['Elapsed'].map(elapsed_to_minutes)
    plot_df['CPUS'] = pd.to_numeric(plot_df['CPUS'], errors='raise')
    if not (np.isfinite(plot_df['CPUS']) & (plot_df['CPUS'] >= 1) & (plot_df['CPUS'] % 1 == 0)).all():
        raise ValueError('Thread counts must be positive integers.')
    plot_df['CPUS'] = plot_df['CPUS'].astype(int)
    # Preserve the original behavior: plot every record, including repeated runs.
    if plot_df.duplicated(['DATASET', 'MARKER', 'CPUS']).any():
        print('Warning: repeated runs detected; all records are plotted without aggregation.')
    plot_df['MARKER'] = pd.Categorical(plot_df['MARKER'], categories=MARKER_ORDER, ordered=True)
    plot_df['DATASET'] = pd.Categorical(plot_df['DATASET'], categories=DATASET_ORDER, ordered=True)
    plot_df.sort_values(['DATASET', 'MARKER', 'CPUS'], inplace=True)
    max_cpus = int(plot_df['CPUS'].max())
    max_time = max(0.1, float(np.ceil(plot_df['TIME_MIN'].max() * 10) / 10))
    x_breaks, y_breaks = compute_breaks(max_cpus, max_time)
    x_breaks = sorted(set(x_breaks) | set(plot_df['CPUS']))
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Arial', 'Liberation Sans', 'DejaVu Sans', 'sans-serif']
    fig, ax = plt.subplots(figsize=(13, 16))
    ax.axvline(1, color='black', linewidth=0.4)
    ax.axhline(0, color='black', linewidth=0.4)
    label_entries = []
    for dataset in DATASET_ORDER:
        dataset_data = plot_df[plot_df['DATASET'] == dataset]
        for marker in MARKER_ORDER:
            marker_data = dataset_data[dataset_data['MARKER'] == marker].sort_values('CPUS')
            if marker_data.empty:
                continue
            ax.plot(marker_data['CPUS'], marker_data['TIME_MIN'], color=DATASET_COLORS[dataset], linestyle=LINESTYLE_BY_MARKER[marker], linewidth=2.2, marker='o', markersize=5)
            for _, row in marker_data.iterrows():
                label_y = min(float(row['TIME_MIN']) * 1.07, max_time * 0.995)
                text = ax.text(row['CPUS'], label_y, format_duration_label(row['TIME_MIN']), fontsize=10, color='0.2', bbox={'boxstyle': 'round,pad=0.2', 'fc': (1, 1, 1, 0.5), 'ec': 'none'})
                label_entries.append((text, float(row['CPUS']), label_y))
    overlap_groups = {}
    for text, x_val, y_val in label_entries:
        key = (int(round(np.log2(x_val) * 10)), int(round(np.log10(max(y_val, 1e-6)) * 20)))
        overlap_groups.setdefault(key, []).append((text, x_val, y_val))
    overlap_texts = []
    for group in overlap_groups.values():
        if len(group) < 2:
            continue
        for idx, (text, x_val, y_val) in enumerate(sorted(group, key=lambda item: item[2])):
            text.set_position((x_val, min(y_val * (1 + 0.12 * idx), max_time * 0.995)))
            overlap_texts.append(text)
    ax.set_xscale('log', base=2)
    ax.set_xticks(x_breaks)
    ax.set_xlim(1, max(1.1, max(x_breaks)))
    ax.set_xticklabels([str(x) for x in x_breaks])
    ax.set_yscale('symlog', base=10, linthresh=1)
    ax.set_ylim(0, max_time)
    ax.set_yticks(y_breaks)
    ax.set_yticklabels([format_duration_label(y) for y in y_breaks])
    ax.grid(True, which='major', color='gray', alpha=1.0)
    ax.grid(False, which='minor')
    ax.set_xlabel('\nNumber of threads (log2 scale)', fontsize=14)
    ax.set_ylabel('Computation Time (symlog scale)\n', fontsize=14)
    ax.set_title('Computation time by thread count\n', fontsize=18, pad=2)
    present_datasets = [d for d in DATASET_ORDER if (plot_df['DATASET'] == d).any()]
    add_horizontal_top_legends(fig, present_datasets)
    fig.subplots_adjust(left=0.09, right=0.93, bottom=0.08, top=0.88)
    # Adjust labels after final axis transformations and layout.
    if adjust_text is not None and overlap_texts:
        adjust_text(overlap_texts, ax=ax, expand=(1.38, 1.6), force_text=(0.7, 0.9), force_static=(0.42, 0.56), iter_lim=4000, arrowprops={'arrowstyle': '-', 'color': '0.6', 'lw': 0.5})
    fig.savefig(output_stem.with_suffix('.svg'))
    fig.savefig(output_stem.with_suffix('.png'), dpi=300)
    fig.savefig(output_stem.with_suffix('.pdf'))
    plt.close(fig)
    print(f'Saved {output_stem.with_suffix(".svg")}, {output_stem.with_suffix(".png")}, and {output_stem.with_suffix(".pdf")}')


if __name__ == '__main__':
    main()
