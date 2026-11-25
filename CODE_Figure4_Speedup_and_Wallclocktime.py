#!/usr/bin/env python3
"""Generate strong-scaling PDF and PNG figures from publication benchmark CSV."""

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATASET_ORDER = [
    ("benchmark_ZhangNNEtAl2025_53angiosperms", "Zhang et al. (53 angiosperms)"),
    ("benchmark_YangEtAl2022_Asteraceae", "Yang et al. (Asteraceae)"),
    ("benchmark_YangEtAl2022_monocots", "Yang et al. (Monocots)"),
    ("benchmark_YangEtAl2022_angiosperms", "Yang et al. (Angiosperms)"),
    ("benchmark_ZhangNNEtAl2025_13724angiosperms", "Zhang et al. (13,724 angiosperms)"),
]
MODES = ["cds", "int", "igs"]
THREADS = [1, 2, 4, 8, 16, 32]
PALETTE = ["#1b9e77", "#d95f02", "#7570b3", "#e7298a", "#66a61e"]


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


def make_plots(publication_csv: Path, out_dir: Path) -> None:
    pub = load_csv(publication_csv)
    out_dir.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 3, figsize=(14, 8.2), sharex=True)

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
        ax_wall.grid(True, which="both", alpha=0.25)

    # Gather legend entries across all panels, even if the first panel lacks a dataset.
    legend_items = {}
    for ax in axes.flat:
        handles, labels = ax.get_legend_handles_labels()
        for handle, label in zip(handles, labels):
            legend_items.setdefault(label, handle)
    fig.legend(
        list(legend_items.values()),
        list(legend_items.keys()),
        loc="upper center",
        ncol=3,
        frameon=False,
        bbox_to_anchor=(0.5, 1.01),
    )
    fig.tight_layout(rect=[0, 0, 1, 0.91])
    for ext in ("pdf", "png"):
        output = out_dir / f"figure_strong_scaling.{ext}"
        fig.savefig(output, dpi=300, bbox_inches="tight")
        print(f"Wrote {output}")
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pub-csv", type=Path, default=Path("publication_summary_metrics.csv")
    )
    parser.add_argument(
        "--out-dir", type=Path, default=Path("VIZ_Figure4_Speedup_and_Wallclocktime")
    )
    args = parser.parse_args()
    make_plots(args.pub_csv, args.out_dir)

# python CODE_Figure4_Speedup_and_Wallclocktime.py --pub-csv DATA_Benchmarking_on_Workstation__2026_11_24.csv
