from pathlib import Path
import argparse

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, LogLocator


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
    "benchmark_ZhangNNEtAl2025_53angiosperms": "Angiosperms (n=53)",
    "benchmark_YangEtAl2022_Asteraceae": "Asteraceae (n=155)",
    "benchmark_YangEtAl2022_monocots": "Monocot (n=733)",
    "benchmark_YangEtAl2022_angiosperms": "Angiosperms (n=2,585)",
    "benchmark_ZhangNNEtAl2025_13724angiosperms": "Angiosperms (n=13,724)",
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
        description="Create combined speedup and memory scaling figures."
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
        default="Vis/factors_across_datasets",
        help="Output path stem; script writes *_speedup and *_memory files.",
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
        sorted_grp = grp.sort_values("threads")
        for _, row in sorted_grp.iterrows():
            rows.append(
                {
                    "dataset": dataset,
                    "marker": marker,
                    "threads": row["threads"],
                    "speedup": baseline / row["elapsed_seconds"],
                    "speedup_percent": ((baseline / row["elapsed_seconds"]) - 1.0) * 100.0,
                }
            )

    return pd.DataFrame(rows)


def make_dataset_color_map(datasets: list[str]) -> dict[str, str]:
    color_map = {}
    default_cycle = plt.rcParams["axes.prop_cycle"].by_key().get("color", [])

    for idx, dataset in enumerate(datasets):
        if dataset in DATASET_COLORS:
            color_map[dataset] = DATASET_COLORS[dataset]
        else:
            color_map[dataset] = default_cycle[idx % len(default_cycle)] if default_cycle else "gray"

    return color_map


def apply_common_axes_style(ax: plt.Axes, max_threads: int) -> None:
    x_breaks = [1, 2, 4, 8, 16, 32]
    x_breaks = [x for x in x_breaks if x <= max_threads]
    if max_threads not in x_breaks:
        x_breaks.append(max_threads)

    ax.set_xscale("log", base=2)
    ax.set_xticks(sorted(set(x_breaks)))
    ax.get_xaxis().set_major_formatter(plt.ScalarFormatter())
    ax.grid(True, which="major", alpha=0.3)


def add_legends(ax: plt.Axes, datasets: list[str], dataset_colors: dict[str, str]) -> None:
    dataset_handles = [
        Line2D([0], [0], color=dataset_colors[d], lw=2.5, label=DATASET_LABELS.get(d, d.replace("benchmark_", "")))
        for d in datasets
    ]
    marker_handles = [
        Line2D([0], [0], color="black", lw=2.5, linestyle=LINESTYLE_BY_MARKER[m], label=m)
        for m in MARKER_ORDER
    ]

    legend_datasets = ax.legend(
        handles=dataset_handles,
        title="Dataset",
        loc="upper left",
        bbox_to_anchor=(1.01, 1.0),
    )
    ax.add_artist(legend_datasets)
    ax.legend(
        handles=marker_handles,
        title="Marker",
        loc="upper left",
        bbox_to_anchor=(1.01, 0.56),
    )


def add_horizontal_top_legends(fig: plt.Figure, datasets: list[str], dataset_colors: dict[str, str]) -> None:
    dataset_prefix = Line2D([], [], linestyle="None", label="DATASET")
    dataset_handles = [
        Line2D(
            [0],
            [0],
            color=dataset_colors[d],
            lw=2.8,
            marker="o",
            markersize=6,
            label=DATASET_LABELS.get(d, d.replace("benchmark_", "")),
        )
        for d in datasets
    ]
    marker_prefix = Line2D([], [], linestyle="None", label="MARKER")
    marker_handles = [
        Line2D([0], [0], color="black", lw=2.8, linestyle=LINESTYLE_BY_MARKER[m], label=m)
        for m in ["CDS", "INT", "IGS"]
    ]

    dataset_legend = fig.legend(
        handles=[dataset_prefix, *dataset_handles],
        loc="upper center",
        bbox_to_anchor=(0.5, 0.985),
        ncol=max(1, len(dataset_handles) + 1),
        columnspacing=0.9,
        handletextpad=0.5,
        labelspacing=0.4,
        handlelength=2.6,
        frameon=False,
    )
    fig.add_artist(dataset_legend)

    fig.legend(
        handles=[marker_prefix, *marker_handles],
        loc="upper center",
        bbox_to_anchor=(0.5, 0.935),
        ncol=4,
        columnspacing=0.9,
        handletextpad=0.5,
        labelspacing=0.4,
        handlelength=2.6,
        frameon=False,
    )


def plot_panel(
    ax: plt.Axes,
    plot_df: pd.DataFrame,
    value_col: str,
    y_label: str,
    title: str,
    dataset_colors: dict[str, str],
    is_memory_panel: bool = False,
) -> None:
    max_threads = int(plot_df["threads"].max())
    datasets = sorted(plot_df["dataset"].unique())

    for dataset in datasets:
        for marker in MARKER_ORDER:
            sub = plot_df[
                (plot_df["dataset"] == dataset)
                & (plot_df["marker"] == marker)
            ].sort_values("threads")

            if sub.empty:
                continue

            ax.plot(
                sub["threads"],
                sub[value_col],
                color=dataset_colors[dataset],
                linestyle=LINESTYLE_BY_MARKER[marker],
                linewidth=2.2,
                marker="o",
                markersize=5,
            )

    if value_col == "speedup":
        # x_ideal = sorted(plot_df["threads"].unique())
        # ax.plot(
        #     x_ideal,
        #     x_ideal,
        #     color="black",
        #     linestyle="dashdot",
        #     linewidth=1.5,
        #     alpha=0.8,
        # )
        pass

    apply_common_axes_style(ax, max_threads=max_threads)
    if is_memory_panel:
        ax.set_yscale("log", base=10)
        ax.yaxis.set_major_locator(LogLocator(base=10.0, subs=(1.0,)))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}"))

    ax.set_xlabel("Number of CPUs (log2 scale)")
    ax.set_ylabel(y_label)
    ax.set_title(title)


def plot_side_by_side(
    speedup_df: pd.DataFrame,
    memory_df: pd.DataFrame,
    output_stem: Path,
) -> None:
    all_datasets = [d for d in DATASET_ORDER if d in set(memory_df["dataset"].unique())]
    dataset_colors = make_dataset_color_map(all_datasets)

    fig, axes = plt.subplots(1, 2, figsize=(15, 7.5))

    plot_panel(
        ax=axes[0],
        plot_df=speedup_df,
        value_col="speedup_percent",
        y_label="Speedup (%)",
        title="Speed Improvements Through Parallelization",
        dataset_colors=dataset_colors,
    )

    plot_panel(
        ax=axes[1],
        plot_df=memory_df,
        value_col="max_ram_gb",
        y_label="Peak RAM (GB)",
        title="Memory Scaling Across Datasets",
        dataset_colors=dataset_colors,
        is_memory_panel=True,
    )

    axes[0].text(
        -0.07,
        1.06,
        "A",
        transform=axes[0].transAxes,
        fontsize=22,
        fontweight="bold",
        va="top",
        ha="left",
    )
    axes[1].text(
        -0.07,
        1.06,
        "B",
        transform=axes[1].transAxes,
        fontsize=22,
        fontweight="bold",
        va="top",
        ha="left",
    )

    add_horizontal_top_legends(fig, datasets=all_datasets, dataset_colors=dataset_colors)

    fig.subplots_adjust(left=0.055, right=0.985, top=0.80, bottom=0.11, wspace=0.14)
    out_png = output_stem.with_name(f"{output_stem.name}.png")
    out_svg = output_stem.with_name(f"{output_stem.name}.svg")
    fig.savefig(out_png, dpi=300)
    fig.savefig(out_svg)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    input_csv = Path(args.input_csv)
    output_stem = Path(args.output_path_stem)

    if not input_csv.exists():
        raise FileNotFoundError(f"Input file does not exist: {input_csv}")

    ensure_output_dir(output_stem)

    df = pd.read_csv(input_csv)
    df["marker"] = df["marker"].astype(str).str.upper()
    df = df[df["marker"].isin(MARKER_ORDER)].copy()
    df = df[df["dataset"].isin(DATASET_ORDER)].copy()

    speedup_df = build_speedup_df(df)

    plot_side_by_side(
        speedup_df=speedup_df,
        memory_df=df,
        output_stem=output_stem,
    )

if __name__ == "__main__":
    main()
