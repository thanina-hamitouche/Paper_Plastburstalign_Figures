from pathlib import Path
import argparse

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

try:
    from adjustText import adjust_text
except ImportError:  # pragma: no cover
    adjust_text = None

MARKER_ORDER = ["CDS", "INT", "IGS"]
LINESTYLE_BY_MARKER = {
    "CDS": "solid",
    "INT": "dashed",
    "IGS": "dotted",
}

DATASET_ORDER = [
    "benchmark_ZhangNNEtAl2025_53angiosperms",
    "benchmark_YangEtAl2022_Asteraceae",
    "benchmark_YangEtAl2022_monocots",
    "benchmark_YangEtAl2022_angiosperms",
    "benchmark_ZhangNNEtAl2025_13724angiosperms",
]

DATASET_LABELS = {
    "benchmark_ZhangNNEtAl2025_53angiosperms": "Angiosperms (n=53)",
    "benchmark_YangEtAl2022_Asteraceae": "Asteraceae (n=155)",
    "benchmark_YangEtAl2022_monocots": "Monocot (n=733)",
    "benchmark_YangEtAl2022_angiosperms": "Angiosperms (n=2,585)",
    "benchmark_ZhangNNEtAl2025_13724angiosperms": "Angiosperms (n=13,724)",
}

DATASET_COLORS = {
    "benchmark_ZhangNNEtAl2025_53angiosperms": "#377eb8",
    "benchmark_YangEtAl2022_Asteraceae": "#4daf4a",
    "benchmark_YangEtAl2022_monocots": "#984ea3",
    "benchmark_YangEtAl2022_angiosperms": "#ff7f00",
    "benchmark_ZhangNNEtAl2025_13724angiosperms": "#e41a1c",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create speed-improvement figure from benchmark CSV data."
    )
    parser.add_argument(
        "input_csv",
        nargs="?",
        default="./input_data/plastburst_benchmark_Final.csv",
        help="Input CSV file path.",
    )
    parser.add_argument(
        "output_path_stem",
        nargs="?",
        default="./VIZ_SpeedImprovements/PlastomeBurst_SpeedImprovements_AllMarkers",
        help="Output path stem; script writes .png and .svg files.",
    )
    return parser.parse_args()


def ensure_output_dir(output_stem: Path) -> None:
    output_stem.parent.mkdir(parents=True, exist_ok=True)


def format_duration_label(x_min: float) -> str:
    if pd.isna(x_min):
        return ""

    if x_min < 1:
        return f"{int(round(x_min * 60))} sec"

    if x_min > 60:
        total_minutes = int(round(x_min))
        hours = total_minutes // 60
        minutes = total_minutes - (hours * 60)
        if minutes == 0:
            return f"{hours} h"
        return f"{hours} h {minutes} min"

    rounded = round(x_min, 1)
    text = f"{rounded:.1f}"
    if text.endswith(".0"):
        text = text[:-2]
    return f"{text} min"


def compute_breaks(max_cpus: int, max_time_min: float) -> tuple[list[int], list[float]]:
    x_breaks = sorted({2 ** i for i in range(int(np.ceil(np.log2(max_cpus))) + 1) if 2 ** i <= max_cpus})
    if max_cpus not in x_breaks:
        x_breaks.append(max_cpus)

    y_breaks_base = [0, 0.5, 1, 5, 10, 20, 40, 60, 120, 240]
    if max_time_min > max(y_breaks_base):
        extra_count = int(np.ceil(np.log(max_time_min / 240.0) / np.log(2.0)))
        y_breaks_extra = [240 * (2 ** i) for i in range(1, extra_count + 1)]
        y_breaks = sorted(set(y_breaks_base + y_breaks_extra))
    else:
        y_breaks = y_breaks_base

    y_breaks = [value for value in y_breaks if value <= max_time_min]
    return x_breaks, y_breaks


def add_horizontal_top_legends(fig: plt.Figure, datasets: list[str]) -> None:
    dataset_prefix = Line2D([], [], linestyle="None", label="DATASET")
    dataset_handles = [
        Line2D(
            [0],
            [0],
            color=DATASET_COLORS[d],
            lw=2.8,
            marker="o",
            markersize=6,
            label=DATASET_LABELS[d],
        )
        for d in datasets
    ]
    marker_prefix = Line2D([], [], linestyle="None", label="MARKER")
    marker_handles = [
        Line2D([0], [0], color="black", lw=2.8, linestyle=LINESTYLE_BY_MARKER[m], label=m)
        for m in MARKER_ORDER
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
        bbox_to_anchor=(0.5, 0.955),
        ncol=4,
        columnspacing=0.9,
        handletextpad=0.5,
        labelspacing=0.4,
        handlelength=2.6,
        frameon=False,
    )


def main() -> None:
    args = parse_args()
    input_csv = Path(args.input_csv)
    output_stem = Path(args.output_path_stem)

    if not input_csv.exists():
        raise FileNotFoundError(f"Input file does not exist: {input_csv}")

    ensure_output_dir(output_stem)

    plot_df = pd.read_csv(input_csv)
    plot_df["MARKER"] = plot_df["MARKER"].astype(str).str.upper()
    plot_df = plot_df[plot_df["MARKER"].isin(MARKER_ORDER)].copy()
    plot_df = plot_df[plot_df["DATASET"].isin(DATASET_ORDER)].copy()
    plot_df["TIME_MIN"] = plot_df["TIME"] / 60.0

    plot_df["MARKER"] = pd.Categorical(plot_df["MARKER"], categories=MARKER_ORDER, ordered=True)
    plot_df["DATASET"] = pd.Categorical(plot_df["DATASET"], categories=DATASET_ORDER, ordered=True)
    plot_df.sort_values(["DATASET", "MARKER", "CPUS"], inplace=True)

    max_cpus = int(plot_df["CPUS"].max())
    max_time = float(np.ceil(plot_df["TIME_MIN"].max() * 10.0) / 10.0)
    x_breaks, y_breaks = compute_breaks(max_cpus=max_cpus, max_time_min=max_time)

    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["Arial", "Liberation Sans", "DejaVu Sans", "sans-serif"]
    fig, ax = plt.subplots(figsize=(13, 16))

    ax.axvline(1, color="black", linewidth=0.4)
    ax.axhline(0, color="black", linewidth=0.4)

    label_entries: list[tuple[plt.Text, float, float]] = []
    for dataset in DATASET_ORDER:
        dataset_data = plot_df[plot_df["DATASET"] == dataset]
        if dataset_data.empty:
            continue

        for marker in MARKER_ORDER:
            marker_data = dataset_data[dataset_data["MARKER"] == marker].sort_values("CPUS")
            if marker_data.empty:
                continue

            ax.plot(
                marker_data["CPUS"],
                marker_data["TIME_MIN"],
                color=DATASET_COLORS[dataset],
                linestyle=LINESTYLE_BY_MARKER[marker],
                linewidth=2.2,
                marker="o",
                markersize=5,
            )

            for _, row in marker_data.iterrows():
                label_y = min(float(row["TIME_MIN"]) * 1.07, max_time * 0.995)
                text = ax.text(
                    row["CPUS"],
                    label_y,
                    format_duration_label(float(row["TIME_MIN"])),
                    fontsize=10,
                    color="0.2",
                    bbox={"boxstyle": "round,pad=0.2", "fc": (1, 1, 1, 0.5), "ec": "none"},
                )
                label_entries.append((text, float(row["CPUS"]), label_y))

    overlap_groups: dict[tuple[int, int], list[tuple[plt.Text, float, float]]] = {}
    for text, x_val, y_val in label_entries:
        x_key = int(round(np.log2(max(x_val, 1e-9)) * 10.0))
        y_key = int(round(np.log10(max(y_val, 1e-6)) * 20.0))
        overlap_groups.setdefault((x_key, y_key), []).append((text, x_val, y_val))

    overlap_texts: list[plt.Text] = []
    for group_entries in overlap_groups.values():
        if len(group_entries) < 2:
            continue
        for idx, (text, x_val, y_val) in enumerate(sorted(group_entries, key=lambda item: item[2])):
            shifted_y = min(y_val * (1.0 + 0.12 * idx), max_time * 0.995)
            text.set_position((x_val, shifted_y))
            overlap_texts.append(text)

    if adjust_text is not None and overlap_texts:
        adjust_text(
            overlap_texts,
            ax=ax,
            expand_points=(1.38, 1.6),
            expand_text=(1.6, 1.85),
            force_text=(0.7, 0.9),
            force_points=(0.42, 0.56),
            iter_lim=4000,
            arrowprops={"arrowstyle": "-", "color": "0.6", "lw": 0.5},
        )

    ax.set_xscale("log", base=2)
    ax.set_xticks(x_breaks)
    ax.set_xlim(1, max(x_breaks))
    ax.set_xticklabels([str(x) for x in x_breaks])

    # symlog approximates ggplot pseudo-log while still allowing y=0.
    ax.set_yscale("symlog", base=10, linthresh=1)
    ax.set_ylim(0, max_time)
    ax.set_yticks(y_breaks)
    ax.set_yticklabels([format_duration_label(y) for y in y_breaks])

    ax.grid(True, which="major", color="gray", alpha=1.0)
    ax.grid(False, which="minor")

    ax.set_xlabel("\nNumber of CPUs (log2 scale)", fontsize=14)
    ax.set_ylabel("Computation Time (log10 scale)\n", fontsize=14)
    ax.set_title("Speed improvements through MPI implementation\n", fontsize=18, pad=2)

    present_datasets = [d for d in DATASET_ORDER if d in set(plot_df["DATASET"].astype(str).unique())]
    add_horizontal_top_legends(fig, datasets=present_datasets)

    fig.subplots_adjust(left=0.09, right=0.93, bottom=0.08, top=0.88)

    fig.savefig(output_stem.with_suffix(".svg"))
    fig.savefig(output_stem.with_suffix(".png"), dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    main()
