#!/usr/bin/env python3
"""Plot wall-clock time, speedup, efficiency and peak RSS for each dataset.

Figure: 4 rows (Wall-clock time, Speedup, Efficiency, Peak RSS), with one
column per dataset. Each panel contains one line per extraction mode.

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
import math
from pathlib import Path
from textwrap import fill

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter

from CODE_SupplFig2_Benchmarking_Workstation__by_extraction_mode import (
    DATASETS,
    MODES,
    add_row_labels,
    dataset_color,
    load_metrics,
)
from figure_export_helper import (
    TYPOGRAPHY,
    add_bottom_legend,
    configure_typography,
    dated_output_paths,
    fit_bbox_to_aspect,
    prepare_figure,
    report_output_directory,
)

MODE_STYLES = {
    "cds": ("o", "solid"),
    "int": ("s", "dashed"),
    "igs": ("^", "dotted"),
}


def create_figure(data, output: Path, dpi: int):
    configure_typography(font_size_increase=6)
    if dpi < 300:
        raise ValueError("DPI must be at least 300 for publication output")
    seen = {dataset for (dataset, _mode) in data}
    datasets = [(key, label) for key, label in DATASETS if key in seen]
    datasets.extend((key, key) for key in sorted(seen - {k for k, _ in DATASETS}))
    if not datasets:
        raise ValueError("No supported data in CSV")

    fig, axes = plt.subplots(
        4, len(datasets), figsize=(14 * len(datasets) / 3, 19.6),
        squeeze=False, sharey="row",
    )
    row_titles = ["Wall-clock time", "Speedup", "Parallel efficiency", "Peak memory"]
    all_threads = sorted({threads for runs in data.values() for threads in runs})
    for ri, heading in enumerate(row_titles):
        for ci, (dataset, dataset_label) in enumerate(datasets):
            ax = axes[ri, ci]
            if ri == 0:
                ax.set_title(
                    fill(dataset_label, width=20), fontweight="bold", pad=12,
                    fontsize=TYPOGRAPHY["title_size"] + 7,
                )
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
                ax.set_ylabel("Wall-clock time (log10)" if ci == 0 else "", labelpad=3)
                ax.set_yscale("log")
                ax.grid(True, which="both", alpha=0.25)
            elif ri == 1:
                ax.set_ylabel("Speedup" if ci == 0 else "", labelpad=3)
            elif ri == 2:
                ax.set_ylabel("Efficiency" if ci == 0 else "", labelpad=3)
            else:
                ax.set_ylabel("Peak RSS (log10)" if ci == 0 else "", labelpad=3)
                ax.set_yscale("log", base=10)
                ax.yaxis.set_major_locator(LogLocator(base=10))
                ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _pos: f"{v:g}"))
                ax.yaxis.set_minor_formatter(NullFormatter())

            ax.yaxis.label.set_fontsize(TYPOGRAPHY["axis_label_size"] + 7)

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

            for mode in MODES:
                runs = data.get((dataset, mode), {})
                if not runs:
                    continue
                xs = sorted(runs)
                if ri in (1, 2) and 1 not in runs:
                    print(
                        f"Warning: no 1-thread baseline for {dataset} / {mode.upper()}, skipping speedup/efficiency"
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
                marker, linestyle = MODE_STYLES[mode]
                ax.plot(
                    xs,
                    ys,
                    marker=marker,
                    color=dataset_color(ci, dataset, len(datasets)),
                    linestyle=linestyle,
                    linewidth=1.8 if ri in (0, 3) else 1.7,
                    markersize=5 if ri == 0 else 4.5,
                )

    handles = [
        Line2D(
            [0],
            [0],
            color="black",
            marker=MODE_STYLES[mode][0],
            linestyle=MODE_STYLES[mode][1],
            lw=1.8,
            label=mode,
        )
        for mode in MODES
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
    legend = add_bottom_legend(fig, handles, ncol=4, fontsize=TYPOGRAPHY["axis_label_size"] + 9)
    fig.supxlabel("Threads (log2)", y=0.15, fontsize=TYPOGRAPHY["axis_label_size"] + 9)
    add_row_labels(axes[:, 0], fontsize=22)
    fig.align_ylabels(axes[:, 0])
    fig.tight_layout(rect=(0, 0.12, 1, 1), h_pad=1.8, w_pad=1.8)
    # Subplot spacing is a fraction of panel height; match gaps in physical units.
    column_gap = fig.subplotpars.wspace * axes[0, 0].get_position().width
    row_gap = column_gap * fig.get_figwidth() / fig.get_figheight()
    row_height = (fig.subplotpars.top - fig.subplotpars.bottom - (len(axes) - 1) * row_gap) / len(axes)
    if row_height <= 0:
        raise ValueError("Figure is too small to fit the requested subplot spacing")
    fig.subplots_adjust(hspace=row_gap / row_height)
    ratio_width = 26 * len(datasets)
    aspect_ratio = ratio_width / 99
    bbox = prepare_figure(
        fig, 4 * len(datasets), bbox_inches="tight", bottom_legend=legend,
        aspect_ratio=aspect_ratio, label_gap=None, legend_gap=22,
    )
    pixel_units = math.ceil(bbox.width * dpi / ratio_width)
    bbox = fit_bbox_to_aspect(
        bbox, aspect_ratio, minimum_width=(ratio_width * pixel_units + 0.25) / dpi
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
        default=Path("pub_artifacts/Figure5_Benchmarking_Workstation__by_dataset"),
    )
    parser.add_argument("--dpi", type=int, default=300, help="Export resolution (minimum: 300 dpi).")
    args = parser.parse_args()
    create_figure(load_metrics(args.input_csv), args.output_prefix, args.dpi)


if __name__ == "__main__":
    main()
