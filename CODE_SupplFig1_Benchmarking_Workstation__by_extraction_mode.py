#!/usr/bin/env python3
"""Plot wall-clock time, speedup, efficiency and peak RSS for each alignment mode.

Figure: 4 rows (Wall-clock time, Speedup, Efficiency, Peak RSS) x 3 columns
(cds, int, igs). Each panel contains one line per dataset.

Input CSV required columns:
  dataset,threads,mode,Elapsed,MaxRSS_KB
Additional columns are ignored.

Elapsed accepts numeric seconds, MM:SS, or HH:MM:SS.
Speedup = T_1 / T_p; efficiency = 100 * speedup / p.
A 1-thread baseline is required for speedup and efficiency for each
(dataset, mode) combination. Duplicate thread measurements are rejected.
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

DATASETS = [
    ("benchmark_ZhangNNEtAl2025_53angiosperms", "Zhang et al. 2025 (n=53)"),
    ("benchmark_YangEtAl2022_Asteraceae", "Yang et al. 2022 (n=155)"),
    ("benchmark_YangEtAl2022_monocots", "Yang et al. 2022 (n=733)"),
    ("benchmark_YangEtAl2022_angiosperms", "Yang et al. 2022 (n=2,585)"),
    ("benchmark_ZhangNNEtAl2025_13724angiosperms", "Zhang et al. 2025 (n=13,724)"),
]
MODES = ("cds", "int", "igs")
COLORS = ("#1b9e77", "#d95f02", "#7570b3", "#e7298a", "#66a61e", "#1f78b4", "#a6761d")
DATASET_COLORS = dict(
    zip((key for key, _ in DATASETS), ("#377eb8", "#4daf4a", "#984ea3", "#ff7f00", "#e41a1c"))
)
MARKERS = ("o", "s", "^", "D", "v", "P", "X")


def add_row_labels(axes):
    for index, ax in enumerate(axes):
        ax.annotate(
            chr(ord("A") + index), xy=(0, 1.02), xycoords="axes fraction",
            xytext=(-4, 0), textcoords="offset points", annotation_clip=False,
            fontsize=17, fontweight="bold", ha="right", va="bottom",
        )


def dataset_color(index, key, count):
    if key in DATASET_COLORS:
        return DATASET_COLORS[key]
    if count <= len(COLORS):
        return COLORS[index]
    return plt.get_cmap("tab20")(index / max(1, count - 1))


def parse_elapsed(value: str) -> float:
    value = value.strip()
    if not value:
        raise ValueError("Elapsed is empty")
    parts = value.split(":")
    if len(parts) == 1:
        result = float(value)
    elif len(parts) == 2:
        result = float(parts[0]) * 60 + float(parts[1])
    elif len(parts) == 3:
        result = float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    else:
        raise ValueError(f"Unsupported Elapsed format: {value}")
    if result <= 0:
        raise ValueError(f"Elapsed must be positive: {value}")
    return result


def load_metrics(path: Path):
    data = defaultdict(dict)
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        required = {"dataset", "threads", "mode", "Elapsed", "MaxRSS_KB"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing CSV columns: {', '.join(sorted(missing))}")
        for line_no, r in enumerate(reader, start=2):
            dataset = r["dataset"].strip()
            mode = r["mode"].strip().lower()
            if mode not in MODES:
                print(f"Warning: skipping unsupported mode {mode!r} at line {line_no}")
                continue
            threads = int(r["threads"])
            if threads < 1:
                raise ValueError(f"Invalid threads at line {line_no}")
            elapsed = parse_elapsed(r["Elapsed"])
            memory_gib = float(r["MaxRSS_KB"]) / 1048576.0
            if memory_gib <= 0:
                raise ValueError(
                    f"MaxRSS_KB must be positive at line {line_no} (log scale)"
                )
            key = (dataset, mode)
            if threads in data[key]:
                raise ValueError(
                    f"Duplicate dataset/mode/threads at line {line_no}: {key}, {threads}"
                )
            data[key][threads] = (elapsed, memory_gib)
    return data


def create_figure(data, output: Path, dpi: int):
    configure_typography(font_size_increase=2)
    if dpi < 300:
        raise ValueError("DPI must be at least 300 for publication output")
    seen = {dataset for (dataset, _mode) in data}
    datasets = [(key, label) for key, label in DATASETS if key in seen]
    datasets.extend((key, key) for key in sorted(seen - {k for k, _ in DATASETS}))
    if not datasets:
        raise ValueError("No supported data in CSV")

    fig, axes = plt.subplots(
        4, 3, figsize=(14, 19.6), squeeze=False, sharey="row"
    )
    row_titles = ["Wall-clock time", "Speedup", "Parallel efficiency", "Peak memory"]
    all_threads = sorted({threads for runs in data.values() for threads in runs})
    for ri, heading in enumerate(row_titles):
        for ci, mode in enumerate(MODES):
            ax = axes[ri, ci]
            if ri == 0:
                ax.set_title(mode, fontweight="bold", pad=12)
            ax.set_xscale("log", base=2)
            ax.set_xticks(all_threads, [str(t) for t in all_threads])
            ax.tick_params(
                axis="x",
                top=False,
                labeltop=False,
                bottom=True,
                labelbottom=True,
            )
            ax.tick_params(axis="y", labelleft=True)
            ax.grid(True, which="major", alpha=0.25)
            ax.set_axisbelow("line" if ri == 0 else True)
            if ri == 0:
                ax.set_ylabel("Wall-clock time (sec., log10)" if ci == 0 else "")
                ax.set_yscale("log")
                ax.grid(True, which="both", alpha=0.25)
            elif ri == 1:
                ax.set_ylabel("Speedup" if ci == 0 else "")
            elif ri == 2:
                ax.set_ylabel("Efficiency (%)" if ci == 0 else "")
            else:
                ax.set_ylabel("Peak RSS (log10)" if ci == 0 else "")
                ax.set_yscale("log", base=10)
                ax.yaxis.set_major_locator(LogLocator(base=10))
                ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _pos: f"{v:g}"))
                ax.yaxis.set_minor_formatter(NullFormatter())

            if ri == 1:
                ax.plot(
                    all_threads,
                    all_threads,
                    "--",
                    color="#777777",
                    lw=1.2,
                    label="Ideal linear",
                )
            if ri == 2:
                ax.axhline(100, color="#777777", linestyle="--", lw=1.1)

            for idx, (key, _label) in enumerate(datasets):
                runs = data.get((key, mode), {})
                if not runs:
                    continue
                xs = sorted(runs)
                if ri in (1, 2) and 1 not in runs:
                    print(
                        f"Warning: no 1-thread baseline for {key} / {mode.upper()}, skipping speedup/efficiency"
                    )
                    continue
                base = runs[1][0] if 1 in runs else None
                if ri == 0:
                    ys = [runs[t][0] for t in xs]
                elif ri == 1:
                    ys = [base / runs[t][0] for t in xs]
                elif ri == 2:
                    ys = [100 * (base / runs[t][0]) / t for t in xs]
                else:
                    ys = [runs[t][1] for t in xs]
                ax.plot(
                    xs,
                    ys,
                    marker=DATASET_MARKERS.get(key, MARKERS[idx % len(MARKERS)]),
                    color=dataset_color(idx, key, len(datasets)),
                    linewidth=1.8 if ri in (0, 3) else 1.7,
                    markersize=5 if ri == 0 else 4.5,
                )

    handles = [
        Line2D(
            [0],
            [0],
            color=dataset_color(i, key, len(datasets)),
            marker=DATASET_MARKERS.get(key, MARKERS[i % len(MARKERS)]),
            lw=1.8,
            label=label,
        )
        for i, (key, label) in enumerate(datasets)
    ]
    handles.append(
        Line2D(
            [0],
            [0],
            color="#777777",
            linestyle="--",
            lw=1.2,
            label="Ideal scaling/efficiency",
        )
    )
    legend = add_bottom_legend(fig, handles, fontsize=TYPOGRAPHY["legend_size"] + 2)
    fig.supxlabel("Threads (log2)", y=0.16, fontsize=TYPOGRAPHY["axis_label_size"] + 2)
    add_row_labels(axes[:, 0])
    fig.align_ylabels(axes[:, 0])
    fig.tight_layout(rect=(0, 0.12, 1, 1), h_pad=1.8, w_pad=1.8)
    # Subplot spacing is a fraction of panel height; match gaps in physical units.
    column_gap = axes[0, 1].get_position().x0 - axes[0, 0].get_position().x1
    row_gap = column_gap * fig.get_figwidth() / fig.get_figheight()
    row_height = (fig.subplotpars.top - fig.subplotpars.bottom - (len(axes) - 1) * row_gap) / len(axes)
    if row_height <= 0:
        raise ValueError("Figure is too small to fit the requested subplot spacing")
    fig.subplots_adjust(hspace=row_gap / row_height)
    bbox = prepare_figure(
        fig, 12, bbox_inches="tight", bottom_legend=legend,
        aspect_ratio=26 / 33, label_gap=None, legend_gap=22,
    )
    pixel_units = math.ceil(bbox.width * dpi / 26)
    bbox = fit_bbox_to_aspect(
        bbox, 26 / 33, minimum_width=(26 * pixel_units + 0.25) / dpi
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    for dest in dated_output_paths(output).values():
        fig.savefig(dest, dpi=dpi, bbox_inches=bbox, pad_inches=0)
    plt.close(fig)
    report_output_directory(output.parent)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-csv", type=Path, required=True, help="Benchmark CSV file")
    parser.add_argument(
        "-o",
        "--output-prefix",
        type=Path,
        default=Path("pub_artifacts/SupplFig1_Benchmarking_Workstation__by_extraction_mode"),
    )
    parser.add_argument("--dpi", type=int, default=300, help="Export resolution (minimum: 300 dpi).")
    args = parser.parse_args()
    create_figure(load_metrics(args.input_csv), args.output_prefix, args.dpi)


if __name__ == "__main__":
    main()
