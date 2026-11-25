#!/usr/bin/env python3
"""Plot peak RSS (log10 GiB) and strong-scaling speedup, grouped by mode.

Layout: 2 rows (memory, speedup) x 3 columns (cds, int, igs).
Each subplot shows one line per dataset. Thread tick labels are at the TOP.

Usage:
    python CODE_SupplFig3_peakMem_speedup.py --input-csv beocat_publication_metrics.csv
    python CODE_SupplFig3_peakMem_speedup.py --input-csv results.csv -o pub_artifacts/per_mode
"""

from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter

from figure_export_helper import (
    DATASET_MARKERS,
    TYPOGRAPHY,
    add_bottom_legend,
    configure_typography,
    dated_output_paths,
    fit_bbox_to_aspect,
    prepare_figure,
    report_output_directory,
)

DATASET_ORDER = [
    ("benchmark_ZhangNNEtAl2025_53angiosperms", "Zhang et al. 2025 (n=53)"),
    ("benchmark_YangEtAl2022_Asteraceae", "Yang et al. 2022 (n=155)"),
    ("benchmark_YangEtAl2022_monocots", "Yang et al. 2022 (n=733)"),
    ("benchmark_YangEtAl2022_angiosperms", "Yang et al. 2022 (n=2,585)"),
    ("benchmark_ZhangNNEtAl2025_13724angiosperms", "Zhang et al. 2025 (n=13,724)"),
]
MODES = ("cds", "int", "igs")
THREADS = (1, 2, 4, 8, 16, 32)
COLORS = ("#1b9e77", "#d95f02", "#7570b3", "#e7298a", "#66a61e")
DATASET_COLORS = dict(
    zip((key for key, _ in DATASET_ORDER), ("#377eb8", "#4daf4a", "#984ea3", "#ff7f00", "#e41a1c"))
)


def elapsed_seconds(value: str) -> float:
    """Accept numeric seconds, MM:SS, or HH:MM:SS."""
    value = value.strip()
    if not value:
        raise ValueError("Empty Elapsed value")
    parts = [float(x) for x in value.split(":")]
    if len(parts) > 3:
        raise ValueError(f"Invalid elapsed time: {value!r}")
    return sum(part * 60**i for i, part in enumerate(reversed(parts)))


def load_rows(path: Path) -> dict:
    data = defaultdict(dict)
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        needed = {"dataset", "mode", "threads", "Elapsed", "MaxRSS_KB"}
        missing = needed - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing CSV columns: {', '.join(sorted(missing))}")
        for line_number, row in enumerate(reader, start=2):
            key = (row["dataset"].strip(), row["mode"].strip().lower())
            threads = int(row["threads"])
            if threads in data[key]:
                raise ValueError(
                    f"Duplicate run at CSV line {line_number}: {key}, {threads} threads"
                )
            elapsed = elapsed_seconds(row["Elapsed"])
            memory = float(row["MaxRSS_KB"]) / 1024**2
            if elapsed <= 0 or memory <= 0 or threads <= 0:
                raise ValueError(
                    f"Nonpositive elapsed, RSS, or threads at line {line_number}"
                )
            data[key][threads] = (elapsed, memory)
    return data


def draw(csv_path: Path, output_prefix: Path) -> None:
    configure_typography()
    data = load_rows(csv_path)
    available = {ds for ds, _ in data}
    datasets = [(key, label) for key, label in DATASET_ORDER if key in available]
    datasets += [
        (key, key) for key in sorted(available - {k for k, _ in DATASET_ORDER})
    ]
    if not datasets:
        raise ValueError("CSV has no dataset rows")

    # Expand the palette if the CSV contains more than five datasets.
    palette = plt.get_cmap("tab20")

    def dataset_color(index, key):
        if key in DATASET_COLORS:
            return DATASET_COLORS[key]
        return COLORS[index] if index < len(COLORS) else palette(index % 20)

    fig, axes = plt.subplots(2, 3, figsize=(14, 7))
    fig.suptitle(f"Data: {csv_path.name}", y=0.995, fontsize=TYPOGRAPHY["annotation_size"])

    for col_idx, mode in enumerate(MODES):
        memory_ax, speed_ax = axes[:, col_idx]
        speed_ax.plot(
            THREADS,
            THREADS,
            color="#777777",
            linestyle="--",
            linewidth=1.2,
            label="Ideal scaling",
            zorder=1,
        )

        for idx, (key, label) in enumerate(datasets):
            runs = data.get((key, mode), {})
            xs = [p for p in THREADS if p in runs]
            if not xs:
                continue
            color = dataset_color(idx, key)
            mem = [runs[p][1] for p in xs]
            memory_ax.plot(
                xs,
                mem,
                marker=DATASET_MARKERS.get(key, "o"),
                markersize=4.5,
                linewidth=1.8,
                linestyle="solid",
                color=color,
                label=label,
            )

            if 1 in runs:
                baseline = runs[1][0]
                speed = [baseline / runs[p][0] for p in xs]
                speed_ax.plot(
                    xs,
                    speed,
                    marker=DATASET_MARKERS.get(key, "o"),
                    markersize=4.5,
                    linewidth=1.8,
                    linestyle="solid",
                    color=color,
                    label=label,
                )
            else:
                print(
                    f"Warning: missing 1-thread baseline for {key} / {mode.upper()}; speedup skipped"
                )

        memory_ax.set_yscale("log", base=10)
        memory_ax.yaxis.set_major_locator(LogLocator(base=10))
        memory_ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:g}"))
        memory_ax.yaxis.set_minor_formatter(NullFormatter())
        memory_ax.set_ylabel("Peak RSS (log10)" if col_idx == 0 else "")
        speed_ax.set_ylabel("Speedup" if col_idx == 0 else "")
        speed_ax.set_ylim(bottom=0)

        memory_ax.set_title(mode, weight="bold", pad=12)
        for ax_idx, ax in enumerate((memory_ax, speed_ax)):
            ax.set_xticks(THREADS, [str(p) for p in THREADS])
            ax.tick_params(
                axis="both", top=False, labeltop=False, bottom=True,
                labelbottom=(ax_idx == 1),
            )
            if ax_idx == 1:
                ax.xaxis.get_major_ticks()[THREADS.index(2)].set_pad(
                    TYPOGRAPHY["tick_label_size"] + 4
                )
            ax.xaxis.set_label_position("bottom")
            ax.set_xlabel("")
            ax.grid(True, which="major", alpha=0.25)
            ax.set_axisbelow(True)

    handles = [
        Line2D(
            [0],
            [0],
            color=dataset_color(i, key),
            linestyle="solid",
            marker=DATASET_MARKERS.get(key, "o"),
            linewidth=1.8,
            label=label,
        )
        for i, (key, label) in enumerate(datasets)
    ]
    handles.append(
        Line2D([0], [0], color="#777777", linestyle="--", label="Ideal scaling")
    )
    legend = add_bottom_legend(fig, handles, ncol=min(3, len(handles)))
    fig.supxlabel("Threads (p)", y=0.16, fontsize=TYPOGRAPHY["axis_label_size"])
    fig.subplots_adjust(hspace=0.45, wspace=0.18, top=0.90, bottom=0.22)

    bbox = prepare_figure(
        fig, 12, bbox_inches="tight", bottom_legend=legend, aspect_ratio=2
    )
    dpi = 300
    # Keep both raster dimensions on the same side of pixel rounding boundaries.
    height_pixels = math.ceil(bbox.height * dpi) + 0.25
    bbox = fit_bbox_to_aspect(bbox, 2, minimum_width=2 * height_pixels / dpi)
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    for path in dated_output_paths(output_prefix).values():
        fig.savefig(path, dpi=dpi, bbox_inches=bbox, pad_inches=0)
    plt.close(fig)
    report_output_directory(output_prefix.parent)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-csv", type=Path, required=True, help="Benchmark CSV input")
    parser.add_argument(
        "-o",
        "--output-prefix",
        type=Path,
        default=Path("pub_artifacts/figure_per_mode_memory_speedup"),
    )
    args = parser.parse_args()
    draw(args.input_csv, args.output_prefix)


if __name__ == "__main__":
    main()
