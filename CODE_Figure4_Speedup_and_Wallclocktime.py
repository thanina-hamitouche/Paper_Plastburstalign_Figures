#!/usr/bin/env python3
"""Generate strong-scaling figures from publication benchmark CSV."""

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from figure_export_helper import (
    TYPOGRAPHY,
    configure_typography,
    dated_output_paths,
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
MODES = ["cds", "int", "igs"]
THREADS = [1, 2, 4, 8, 16, 32]
PALETTE = ["#377eb8", "#4daf4a", "#984ea3", "#ff7f00", "#e41a1c"]


def parse_elapsed(s: str) -> float:
    parts = [float(x) for x in s.strip().split(":")]
    return (
        parts[0] * 3600 + parts[1] * 60 + parts[2]
        if len(parts) == 3
        else parts[0] * 60 + parts[1]
    )


def load_csv(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"CSV file not found: {path}")
    data = defaultdict(dict)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            key = (row["dataset"], row["mode"].lower())
            threads = int(row["threads"])
            if threads in data[key]:
                raise ValueError(
                    f"Duplicate dataset/mode/thread combination: {key}, {threads}"
                )
            data[key][threads] = row
    return data


def make_plots(
    publication_csv: Path, out_dir: Path, output_name: str = "figure_strong_scaling"
) -> None:
    configure_typography()
    pub = load_csv(publication_csv)
    out_dir.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 3, figsize=(14, 7.27), sharex=True)

    for col, mode in enumerate(MODES):
        ax_speed = axes[0, col]
        ax_wall = axes[1, col]
        ax_speed.plot(
            THREADS, THREADS, "--", color="#888888", linewidth=1.1, label="Ideal linear"
        )

        for idx, (ds_key, ds_label) in enumerate(DATASET_ORDER):
            runs = pub.get((ds_key, mode), {})
            xs = [threads for threads in THREADS if threads in runs]
            if not xs:
                continue
            wall = [parse_elapsed(runs[threads]["Elapsed"]) for threads in xs]
            ax_wall.plot(
                xs,
                wall,
                "o-",
                color=PALETTE[idx],
                linewidth=1.8,
                markersize=5,
                label=ds_label,
            )
            if 1 in runs:
                baseline = parse_elapsed(runs[1]["Elapsed"])
                speedup = [baseline / seconds for seconds in wall]
                ax_speed.plot(
                    xs,
                    speedup,
                    "o-",
                    color=PALETTE[idx],
                    linewidth=1.8,
                    markersize=5,
                    label=ds_label,
                )

        ax_speed.set_title(f"{mode.upper()} Strong-Scaling Speedup", fontweight="bold")
        ax_speed.set_ylabel("Speedup ($T_1/T_p$)" if col == 0 else "")
        ax_speed.set_ylim(0, 33)
        ax_speed.grid(True, alpha=0.25)

        ax_wall.set_title(f"{mode.upper()} End-to-End Wall Time", fontweight="bold")
        ax_wall.set_yscale("log")
        ax_wall.set_xlabel("Threads ($p$)")
        ax_wall.set_ylabel("Wall Time (seconds, log scale)" if col == 0 else "")
        ax_wall.set_xticks(THREADS)
        ax_wall.set_xticklabels([str(t) for t in THREADS])
        ax_wall.xaxis.get_major_ticks()[THREADS.index(2)].set_pad(
            TYPOGRAPHY["tick_label_size"] + 4
        )
        ax_wall.grid(True, which="both", alpha=0.25)

    # Gather legend entries across all panels, even if the first panel lacks a dataset.
    legend_items = {}
    for ax in axes.flat:
        handles, labels = ax.get_legend_handles_labels()
        for handle, label in zip(handles, labels):
            legend_items.setdefault(label, handle)
    legend = fig.legend(
        list(legend_items.values()),
        list(legend_items.keys()),
        loc="upper center",
        ncol=3,
        frameon=False,
        borderaxespad=0,
        borderpad=0,
    )
    layout_rect = (0, 0.12, 1, 1)
    fig.tight_layout(rect=layout_rect)
    bbox = prepare_figure(
        fig, 12, bbox_inches="tight", layout={"rect": layout_rect}, bottom_legend=legend,
        aspect_ratio=2,
    )
    for output in dated_output_paths(out_dir / output_name).values():
        fig.savefig(output, dpi=300, bbox_inches=bbox, pad_inches=0)
    plt.close(fig)
    report_output_directory(out_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-csv",
        "--pub-csv",
        type=Path,
        default=Path("publication_summary_metrics.csv"),
    )
    output_options = parser.add_mutually_exclusive_group()
    output_options.add_argument(
        "--out-dir", type=Path, help="Output directory using the default filename."
    )
    output_options.add_argument(
        "-o",
        "--output-prefix",
        type=Path,
        help="Output path with or without extension; a date suffix is added.",
    )
    args = parser.parse_args()
    if args.output_prefix is None:
        out_dir = args.out_dir or Path("VIZ_Figure4_Speedup_and_Wallclocktime")
        make_plots(args.input_csv, out_dir)
    else:
        if not args.output_prefix.name:
            parser.error("--output-prefix must include a filename")
        make_plots(args.input_csv, args.output_prefix.parent, args.output_prefix.name)

# python CODE_Figure4_Speedup_and_Wallclocktime.py --input-csv input_data/DATA_Benchmarking_on_Workstation__2026_11_24.csv
