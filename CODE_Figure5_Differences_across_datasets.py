#!/usr/bin/env python3
"""Plot elapsed time, speedup, efficiency and peak RSS for each alignment mode.

Figure: 3 rows (CDS, INT, IGS) x 4 columns (Elapsed, Speedup,
Efficiency, Peak RSS). Each panel contains one line per dataset.

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
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, LogLocator

from figure_export_helper import dated_output_paths, prepare_figure, report_output_directory

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
    if dpi < 300:
        raise ValueError("DPI must be at least 300 for publication output")
    seen = {dataset for (dataset, _mode) in data}
    datasets = [(key, label) for key, label in DATASETS if key in seen]
    datasets.extend((key, key) for key in sorted(seen - {k for k, _ in DATASETS}))
    if not datasets:
        raise ValueError("No supported data in CSV")

    colors = plt.get_cmap("tab20") if len(datasets) > len(COLORS) else None

    def dataset_color(index, key):
        if key in DATASET_COLORS:
            return DATASET_COLORS[key]
        return (
            COLORS[index]
            if colors is None
            else colors(index / max(1, len(datasets) - 1))
        )

    fig, axes = plt.subplots(3, 4, figsize=(19, 11), squeeze=False)
    column_titles = ["Elapsed time", "Speedup", "Parallel efficiency", "Peak memory"]
    all_threads = sorted({threads for runs in data.values() for threads in runs})
    for ri, mode in enumerate(MODES):
        for ci, heading in enumerate(column_titles):
            ax = axes[ri, ci]
            if ri == 0:
                ax.set_title(heading, fontsize=12, fontweight="bold", pad=12)
            ax.set_xlabel("Threads")
            ax.set_xticks(all_threads)
            ax.tick_params(
                axis="x", top=False, labeltop=False, bottom=True, labelbottom=True
            )
            ax.xaxis.set_label_position("bottom")
            ax.grid(True, which="major", alpha=0.25)
            ax.set_axisbelow(True)
            if ci == 0:
                ax.set_ylabel(f"{mode.upper()}\nElapsed (seconds)", fontweight="medium")
            elif ci == 1:
                ax.set_ylabel("Speedup ($T_1 / T_p$)")
            elif ci == 2:
                ax.set_ylabel("Efficiency (%)")
            else:
                ax.set_ylabel("Peak RSS (GiB, log10)")
                ax.set_yscale("log", base=10)
                ax.yaxis.set_major_locator(LogLocator(base=10))
                ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _pos: f"{v:g}"))
                ax.grid(True, which="minor", alpha=0.10)

            if ci == 1:
                ax.plot(
                    all_threads,
                    all_threads,
                    "--",
                    color="#777777",
                    lw=1.2,
                    label="Ideal linear",
                )
            if ci == 2:
                ax.axhline(100, color="#777777", linestyle="--", lw=1.1)

            for idx, (key, _label) in enumerate(datasets):
                runs = data.get((key, mode), {})
                if not runs:
                    continue
                xs = sorted(runs)
                if ci in (1, 2) and 1 not in runs:
                    print(
                        f"Warning: no 1-thread baseline for {key} / {mode.upper()}, skipping speedup/efficiency"
                    )
                    continue
                base = runs[1][0] if 1 in runs else None
                if ci == 0:
                    ys = [runs[t][0] for t in xs]
                elif ci == 1:
                    ys = [base / runs[t][0] for t in xs]
                elif ci == 2:
                    ys = [100 * (base / runs[t][0]) / t for t in xs]
                else:
                    ys = [runs[t][1] for t in xs]
                ax.plot(
                    xs,
                    ys,
                    marker=MARKERS[idx % len(MARKERS)],
                    color=dataset_color(idx, key),
                    linewidth=1.7,
                    markersize=4.5,
                )

    handles = [
        Line2D(
            [0],
            [0],
            color=dataset_color(i, key),
            marker=MARKERS[i % len(MARKERS)],
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
            label="Ideal speedup / 100% efficiency",
        )
    )
    fig.legend(
        handles=handles,
        loc="upper center",
        ncol=3,
        bbox_to_anchor=(0.5, 1.015),
        frameon=False,
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.935), h_pad=2.2, w_pad=1.8)
    bbox = prepare_figure(fig, 14, bbox_inches="tight")
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
        default=Path("pub_artifacts/figure_per_mode_all_metrics"),
    )
    parser.add_argument("--dpi", type=int, default=300, help="Export resolution (minimum: 300 dpi).")
    args = parser.parse_args()
    create_figure(load_metrics(args.input_csv), args.output_prefix, args.dpi)


if __name__ == "__main__":
    main()
