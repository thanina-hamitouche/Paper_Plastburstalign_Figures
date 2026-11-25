from pathlib import Path
import argparse
from datetime import date

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import LogLocator, ScalarFormatter

MARKER_ORDER = ["CDS", "INT", "IGS"]
LINESTYLE_BY_MARKER = {
    "CDS": "solid",
    "INT": "dashed",
    "IGS": "dotted",
}

DATASET_COLORS = {
    "benchmark_ZhangNNEtAl2025_53angiosperms": "#377eb8",
    "benchmark_YangEtAl2022_Asteraceae": "#4daf4a",
    "benchmark_YangEtAl2022_monocots": "#984ea3",
    "benchmark_YangEtAl2022_angiosperms": "#ff7f00",
    "benchmark_ZhangNNEtAl2025_13724angiosperms": "#e41a1c",
}

DATASET_LABELS = {
    "benchmark_ZhangNNEtAl2025_53angiosperms": "Zhang et al. (2025), n=53",
    "benchmark_YangEtAl2022_Asteraceae": "Yang et al. (2022), n=155",
    "benchmark_YangEtAl2022_monocots": "Yang et al. (2022), n=733",
    "benchmark_YangEtAl2022_angiosperms": "Yang et al. (2022), n=2,585",
    "benchmark_ZhangNNEtAl2025_13724angiosperms": "Zhang et al. (2025), n=13,724",
}

DATASET_ORDER = [
    "benchmark_ZhangNNEtAl2025_53angiosperms",
    "benchmark_YangEtAl2022_Asteraceae",
    "benchmark_YangEtAl2022_monocots",
    "benchmark_YangEtAl2022_angiosperms",
    "benchmark_ZhangNNEtAl2025_13724angiosperms",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a combined dataset scaling grid figure."
    )
    parser.add_argument(
        "input_csv",
        nargs="?",
        default="results.csv",
        help="Input CSV file path (default: results.csv).",
    )
    parser.add_argument(
        "output_path_stem",
        nargs="?",
        default="./VIZ_Figure5_Differences_across_datasets/Figure5_Differences_across_datasets",
        help="Output path stem; script writes .png, .svg, and .pdf files.",
    )
    return parser.parse_args()


def ensure_output_dir(output_stem: Path) -> None:
    output_stem.parent.mkdir(parents=True, exist_ok=True)

def build_speedup_df(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (dataset, marker), grp in df.groupby(["dataset", "marker"]):
        baseline_series = grp.loc[grp["threads"] == 1, "elapsed_seconds"]
        if baseline_series.empty:
            continue

        baseline = baseline_series.iloc[0]
        for _, row in grp.sort_values("threads").iterrows():
            rows.append(
                {
                    "dataset": dataset,
                    "marker": marker,
                    "threads": row["threads"],
                    "speedup_percent": (baseline / row["elapsed_seconds"]) * 100.0,
                }
            )

    return pd.DataFrame(rows)


def style_axis_x(ax: plt.Axes, max_threads: int) -> None:
    x_breaks = [1, 2, 4, 8, 16, 32]
    x_breaks = [x for x in x_breaks if x <= max_threads]
    if max_threads not in x_breaks:
        x_breaks.append(max_threads)

    ax.set_xscale("log", base=2)
    ax.set_xticks(sorted(set(x_breaks)))
    ax.get_xaxis().set_major_formatter(ScalarFormatter())
    ax.grid(True, alpha=0.3)


def style_axis_y(ax: plt.Axes) -> None:
    ax.set_yscale("log", base=10)
    ax.yaxis.set_major_locator(LogLocator(base=10.0, subs=(1.0,)))
    ax.yaxis.set_major_formatter(ScalarFormatter())


def main() -> None:
    args = parse_args()
    input_csv = Path(args.input_csv)
    output_stem = Path(args.output_path_stem)
    output_stem = output_stem.with_name(f"{output_stem.stem}__{date.today():%Y_%m_%d}")

    if not input_csv.exists():
        raise FileNotFoundError(f"Input file does not exist: {input_csv}")

    ensure_output_dir(output_stem)

    df = pd.read_csv(input_csv)
    df["marker"] = df["marker"].astype(str).str.upper()

    speedup_df = build_speedup_df(df)
    df["elapsed_minutes"] = df["elapsed_seconds"] / 60.0

    present_datasets = set(df["dataset"].unique())
    datasets = [dataset for dataset in DATASET_ORDER if dataset in present_datasets]
    n_cols = len(datasets)
    n_rows = 4
    row_specs = [
        ("elapsed_minutes", "Wall-clock time (min, log10)", "Wall-clock time (min, log10)"),
        ("max_ram_gb", "PeakRSS (GB, log10)", "PeakRSS (GiB, log10)"),
        ("speedup_percent", "Speedup (%, log10)", "Speedup (%, log10)"),
        ("cpu_percent", "CPU Utilization (%, log10)", "CPU Utilization (%, log10)"),
    ]

    fig, axes = plt.subplots(
        n_rows,
        n_cols,
        figsize=(3.8 * n_cols, 1.9 * n_cols),
        squeeze=False,
        sharey="row",
    )

    for col, dataset in enumerate(datasets):
        clean_name = dataset.replace("benchmark_", "")
        column_label = DATASET_LABELS.get(dataset, clean_name)
        dataset_color = DATASET_COLORS.get(dataset, "gray")
        subset = df[df["dataset"] == dataset]
        subset_sp = speedup_df[speedup_df["dataset"] == dataset]
        max_threads = int(subset["threads"].max())

        for row, (value_col, y_label, row_title) in enumerate(row_specs):
            ax = axes[row, col]
            plot_df = subset_sp if value_col == "speedup_percent" else subset

            for marker in MARKER_ORDER:
                marker_df = plot_df[plot_df["marker"] == marker].sort_values("threads")
                if marker_df.empty:
                    continue

                ax.plot(
                    marker_df["threads"],
                    marker_df[value_col],
                    marker="o",
                    color=dataset_color,
                    linestyle=LINESTYLE_BY_MARKER[marker],
                    linewidth=1.8,
                    markersize=4,
                )

            if value_col == "speedup_percent":
                ideal_threads = sorted(subset_sp["threads"].unique())
                ideal_speedup = [t * 100.0 for t in ideal_threads]
                ax.plot(ideal_threads, ideal_speedup, "-", linewidth=1.2, color="0.6", alpha=1.0)

            if value_col == "cpu_percent":
                ideal_threads = sorted(subset["threads"].unique())
                ideal_cpu = [t * 100 for t in ideal_threads]
                ax.plot(ideal_threads, ideal_cpu, "-", linewidth=1.2, color="0.6", alpha=1.0)

            style_axis_x(ax, max_threads=max_threads)
            style_axis_y(ax)

            if row == 0:
                ax.set_title(column_label, fontsize=10)
    marker_handles = [
        Line2D([0], [0], color="black", linestyle=LINESTYLE_BY_MARKER[m], marker="o", linewidth=1.8, label=m)
        for m in MARKER_ORDER
    ]
    marker_prefix = Line2D([], [], linestyle="None", label="MARKER")
    fig.legend(
        handles=[marker_prefix, *marker_handles],
        loc="upper center",
        bbox_to_anchor=(0.5, 0.975),
        ncol=4,
        columnspacing=0.9,
        handletextpad=0.5,
        labelspacing=0.4,
        handlelength=2.6,
        frameon=False,
    )

    fig.tight_layout(rect=(0.02, 0.05, 0.99, 0.94))

    for row, (_, y_label, _) in enumerate(row_specs):
        row_box = axes[row, 0].get_position()
        fig.text(0.015, row_box.y0 + row_box.height / 2, y_label, fontsize=10, va="center", ha="left", rotation=90)

    fig.text(0.5, 0.015, "Number of CPUs (log2 scale)", ha="center", va="bottom")

    fig.savefig(output_stem.with_suffix(".png"), dpi=300)
    fig.savefig(output_stem.with_suffix(".svg"))
    fig.savefig(output_stem.with_suffix(".pdf"))
    plt.close(fig)


if __name__ == "__main__":
    main()