import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

from figure_export_helper import (
    DATASET_MARKERS,
    TYPOGRAPHY,
    add_bottom_legend,
    configure_typography,
    dated_output_paths,
    prepare_figure,
    report_output_directory,
)

MARKER_ORDER = ["CDS", "INT", "IGS"]
LINESTYLE_BY_MARKER = {"CDS": "solid", "INT": "dashed", "IGS": "dotted"}
DATASET_ORDER = [
    "benchmark_ZhangNNEtAl2025_53angiosperms",
    "benchmark_YangEtAl2022_Asteraceae",
    "benchmark_YangEtAl2022_monocots",
    "benchmark_YangEtAl2022_angiosperms",
    "benchmark_ZhangNNEtAl2025_13724angiosperms",
]
DATASET_LABELS = dict(
    zip(
        DATASET_ORDER,
        [
            "Zhang et al. 2025 (n=53)",
            "Yang et al. 2022 (n=155)",
            "Yang et al. 2022 (n=733)",
            "Yang et al. 2022 (n=2,585)",
            "Zhang et al. 2025 (n=13,724)",
        ],
    )
)
DATASET_COLORS = dict(
    zip(DATASET_ORDER, ["#377eb8", "#4daf4a", "#984ea3", "#ff7f00", "#e41a1c"])
)
DEFAULT_OUTPUT_STEM = "./VIZ_Figure5_ImpactOfMultithreading_Workstation/Figure5_ImpactOfMultithreading_Workstation"


def parse_args(default_input_csv="results.csv", default_output_stem=DEFAULT_OUTPUT_STEM):
    parser = argparse.ArgumentParser(
        description="Plot computation time from benchmark CSV data."
    )
    parser.add_argument("--input-csv", default=default_input_csv)
    output_options = parser.add_mutually_exclusive_group()
    output_options.add_argument(
        "output_path_stem",
        nargs="?",
        default=default_output_stem,
        help=argparse.SUPPRESS,
    )
    output_options.add_argument(
        "--output-prefix",
        type=Path,
        help="Output path stem; writes .png, .svg, and .pdf files.",
    )
    return parser.parse_args()


def elapsed_to_minutes(value):
    """Convert GNU time m:ss or h:mm:ss to minutes for plotting only."""
    parts = str(value).strip().split(":")
    if len(parts) not in (2, 3):
        raise ValueError(f"Invalid elapsed time: {value!r}")
    try:
        numbers = [float(p) for p in parts]
    except ValueError as exc:
        raise ValueError(f"Invalid elapsed time: {value!r}") from exc
    if (
        not all(np.isfinite(n) and n >= 0 for n in numbers)
        or numbers[-1] >= 60
        or any(not n.is_integer() for n in numbers[:-1])
        or (len(numbers) == 3 and numbers[1] >= 60)
    ):
        raise ValueError(f"Invalid elapsed time: {value!r}")
    return sum(n * 60**i for i, n in enumerate(reversed(numbers))) / 60.0


def format_duration_label(x_min):
    if pd.isna(x_min):
        return ""
    if x_min < 1:
        return f"{int(round(x_min * 60))} sec."
    if x_min >= 60:
        hours, minutes = divmod(int(round(x_min)), 60)
        return f"{hours} h {minutes} min" if minutes else f"{hours} h"
    return f"{x_min:.1f}".removesuffix(".0") + " min"


def compute_breaks(max_cpus, max_time_min):
    x_breaks = sorted(
        {2**i for i in range(int(np.ceil(np.log2(max_cpus))) + 1) if 2**i <= max_cpus}
        | {max_cpus}
    )
    y_breaks = [0, 0.5, 1, 5, 10, 20, 40, 60, 120, 240]
    while y_breaks[-1] < max_time_min:
        y_breaks.append(y_breaks[-1] * 2)
    return x_breaks, [v for v in y_breaks if v <= max_time_min]


def add_horizontal_bottom_legend(fig, datasets):
    dataset_handles = [
        Line2D(
            [0],
            [0],
            color=DATASET_COLORS[d],
            lw=2.8,
            marker=DATASET_MARKERS[d],
            markersize=6,
            label=DATASET_LABELS[d],
        )
        for d in datasets
    ]
    marker_handles = [
        Line2D(
            [0], [0], color="black", lw=2.8, linestyle=LINESTYLE_BY_MARKER[m], label=m.lower()
        )
        for m in MARKER_ORDER
    ]
    rows = []
    for group in (dataset_handles, marker_handles):
        for start in range(0, len(group), 3):
            row = group[start:start + 3]
            row += [Line2D([], [], linestyle="None", label="")] * (3 - len(row))
            rows.append(row)
    handles = [row[column] for column in range(3) for row in rows]
    return add_bottom_legend(fig, handles)


def stack_duration_labels(ax, labels):
    """Stack labels in value order with minimum displacement in display space."""
    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    axes_bounds = ax.get_window_extent(renderer)
    gap = renderer.points_to_pixels(2)
    groups = {}
    for label in labels:
        groups.setdefault(label.xy[0], []).append(label)

    for group in groups.values():
        group.sort(key=lambda label: label.xy[1])
        heights = [label.get_bbox_patch().get_window_extent(renderer).height for label in group]
        offsets = [0.0]
        for previous, current in zip(heights, heights[1:]):
            offsets.append(offsets[-1] + (previous + current) / 2 + gap)
        lower = axes_bounds.y0 + heights[0] / 2 + gap
        upper = axes_bounds.y1 - heights[-1] / 2 - offsets[-1] - gap
        if lower > upper:
            raise ValueError(f"Too many duration labels to fit at thread count {group[0].xy[0]:g}")

        # Isotonic regression keeps the stack ordered while minimizing movement.
        blocks = []
        for label, offset in zip(group, offsets):
            anchor_y = ax.transData.transform(label.xy)[1]
            blocks.append([anchor_y - offset, 1])
            while len(blocks) > 1 and blocks[-2][0] / blocks[-2][1] > blocks[-1][0] / blocks[-1][1]:
                total, count = blocks.pop()
                blocks[-1][0] += total
                blocks[-1][1] += count
        positions = [
            min(upper, max(lower, total / count))
            for total, count in blocks
            for _ in range(count)
        ]
        for label, offset, position in zip(group, offsets, positions):
            anchor_y = ax.transData.transform(label.xy)[1]
            label.set_position((5, (position + offset - anchor_y) * 72 / fig.dpi))

    fig.canvas.draw()
    bounds = [(label.xy[0], label.get_bbox_patch().get_window_extent(renderer)) for label in labels]
    for index, (thread, left) in enumerate(bounds):
        for other_thread, right in bounds[index + 1:]:
            if thread != other_thread and left.overlaps(right):
                raise ValueError(
                    "Duration labels overlap across thread counts; use a wider figure or fewer thread counts"
                )


def main(default_input_csv="results.csv", default_output_stem=DEFAULT_OUTPUT_STEM):
    args = parse_args(default_input_csv, default_output_stem)
    input_csv = Path(args.input_csv)
    output_stem = Path(
        args.output_prefix if args.output_prefix is not None else args.output_path_stem
    )
    output_paths = dated_output_paths(output_stem)
    output_stem.parent.mkdir(parents=True, exist_ok=True)
    plot_df = pd.read_csv(input_csv, dtype={"Elapsed": str})
    required = {"dataset", "threads", "mode", "Elapsed"}
    missing = required - set(plot_df.columns)
    if missing:
        raise ValueError(f"Missing CSV columns: {sorted(missing)}")
    plot_df = plot_df.rename(
        columns={"dataset": "DATASET", "threads": "CPUS", "mode": "MARKER"}
    )
    plot_df["MARKER"] = plot_df["MARKER"].astype(str).str.strip().str.upper()
    plot_df = plot_df[
        plot_df["MARKER"].isin(MARKER_ORDER) & plot_df["DATASET"].isin(DATASET_ORDER)
    ].copy()
    if plot_df.empty:
        raise ValueError("No rows match the configured datasets and markers.")
    plot_df["TIME_MIN"] = plot_df["Elapsed"].map(elapsed_to_minutes)
    plot_df["CPUS"] = pd.to_numeric(plot_df["CPUS"], errors="raise")
    if not (
        np.isfinite(plot_df["CPUS"])
        & (plot_df["CPUS"] >= 1)
        & (plot_df["CPUS"] % 1 == 0)
    ).all():
        raise ValueError("Thread counts must be positive integers.")
    plot_df["CPUS"] = plot_df["CPUS"].astype(int)
    # Preserve the original behavior: plot every record, including repeated runs.
    if plot_df.duplicated(["DATASET", "MARKER", "CPUS"]).any():
        print(
            "Warning: repeated runs detected; all records are plotted without aggregation."
        )
    plot_df["MARKER"] = pd.Categorical(
        plot_df["MARKER"], categories=MARKER_ORDER, ordered=True
    )
    plot_df["DATASET"] = pd.Categorical(
        plot_df["DATASET"], categories=DATASET_ORDER, ordered=True
    )
    plot_df.sort_values(["DATASET", "MARKER", "CPUS"], inplace=True)
    max_cpus = int(plot_df["CPUS"].max())
    max_time = max(0.1, float(np.ceil(plot_df["TIME_MIN"].max() * 10) / 10))
    x_breaks, y_breaks = compute_breaks(max_cpus, max_time)
    x_breaks = sorted(set(x_breaks) | set(plot_df["CPUS"]))
    configure_typography()
    fig, ax = plt.subplots(figsize=(13, 14.4))
    ax.axvline(1, color="black", linewidth=0.4)
    ax.axhline(0, color="black", linewidth=0.4)
    label_entries = []
    for dataset in DATASET_ORDER:
        dataset_data = plot_df[plot_df["DATASET"] == dataset]
        for marker in MARKER_ORDER:
            marker_data = dataset_data[dataset_data["MARKER"] == marker].sort_values(
                "CPUS"
            )
            if marker_data.empty:
                continue
            ax.plot(
                marker_data["CPUS"],
                marker_data["TIME_MIN"],
                color=DATASET_COLORS[dataset],
                linestyle=LINESTYLE_BY_MARKER[marker],
                linewidth=2.2,
                marker=DATASET_MARKERS[dataset],
                markersize=5,
            )
            for _, row in marker_data.iterrows():
                text = ax.annotate(
                    format_duration_label(row["TIME_MIN"]),
                    xy=(float(row["CPUS"]), float(row["TIME_MIN"])),
                    xytext=(5, 0), textcoords="offset points", va="center",
                    annotation_clip=False,
                    fontsize=TYPOGRAPHY["annotation_size"],
                    color="0.2",
                    arrowprops={"arrowstyle": "-", "color": "0.6", "lw": 0.6},
                    bbox={
                        "boxstyle": "round,pad=0.2",
                        "fc": (1, 1, 1, 0.9),
                        "ec": "none",
                    },
                )
                label_entries.append(text)
    ax.set_xscale("log", base=2)
    ax.set_xticks(x_breaks)
    ax.set_xlim(1, max(1.1, max(x_breaks)))
    ax.set_xticklabels([str(x) for x in x_breaks])
    ax.set_yscale("symlog", base=10, linthresh=1)
    ax.set_ylim(0, max_time)
    ax.set_yticks(y_breaks)
    ax.set_yticklabels([format_duration_label(y) for y in y_breaks])
    ax.grid(True, which="major", color="gray", alpha=1.0)
    ax.grid(False, which="minor")
    ax.set_xlabel("\nThreads (log2)", labelpad=2)
    ax.set_ylabel("Wall-clock time (sec., symlog)\n", labelpad=2)
    present_datasets = [d for d in DATASET_ORDER if (plot_df["DATASET"] == d).any()]
    legend = add_horizontal_bottom_legend(fig, present_datasets)
    fig.subplots_adjust(left=0.09, right=0.93, bottom=0.22, top=0.97)
    prepare_figure(fig, 12, bbox_inches="tight", pad_inches=0.03, bottom_legend=legend)
    stack_duration_labels(ax, label_entries)
    fig.canvas.draw()
    bbox = fig.get_tightbbox(fig.canvas.get_renderer()).padded(0.05)
    fig.savefig(output_paths["svg"], bbox_inches=bbox, pad_inches=0)
    fig.savefig(
        output_paths["png"], dpi=300, bbox_inches=bbox, pad_inches=0
    )
    fig.savefig(output_paths["pdf"], bbox_inches=bbox, pad_inches=0)
    plt.close(fig)
    report_output_directory(output_stem.parent)


if __name__ == "__main__":
    main()
