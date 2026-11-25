#!/usr/bin/env python3
"""Plot peak RSS (log10 GiB) and strong-scaling speedup, grouped by mode.

Layout: 3 rows (CDS, INT, IGS) x 2 columns (memory, speedup).
Each subplot shows one line per dataset. Thread tick labels are at the TOP.

Usage:
    python plot_per_mode_memory_speedup.py beocat_publication_metrics.csv
    python plot_per_mode_memory_speedup.py results.csv -o pub_artifacts/per_mode
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
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter

DATASET_ORDER = [
    ("benchmark_ZhangNNEtAl2025_53angiosperms", "Zhang et al. (53 angiosperms)"),
    ("benchmark_YangEtAl2022_Asteraceae", "Yang et al. (Asteraceae)"),
    ("benchmark_YangEtAl2022_monocots", "Yang et al. (Monocots)"),
    ("benchmark_YangEtAl2022_angiosperms", "Yang et al. (Angiosperms)"),
    ("benchmark_ZhangNNEtAl2025_13724angiosperms", "Zhang et al. (13,724 angiosperms)"),
]
MODES = ("cds", "int", "igs")
THREADS = (1, 2, 4, 8, 16, 32)
COLORS = ("#1b9e77", "#d95f02", "#7570b3", "#e7298a", "#66a61e")
STYLES = ("solid", "dashed", "dashdot", "dotted", "solid")


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
    fig, axes = plt.subplots(3, 2, figsize=(14, 11.5))

    for row_idx, mode in enumerate(MODES):
        memory_ax, speed_ax = axes[row_idx]
        speed_ax.plot(
            THREADS,
            THREADS,
            color="#777777",
            linestyle="--",
            linewidth=1.2,
            label="Ideal linear",
            zorder=1,
        )

        for idx, (key, label) in enumerate(datasets):
            runs = data.get((key, mode), {})
            xs = [p for p in THREADS if p in runs]
            if not xs:
                continue
            color = COLORS[idx] if idx < len(COLORS) else palette(idx % 20)
            style = STYLES[idx % len(STYLES)]
            mem = [runs[p][1] for p in xs]
            memory_ax.plot(
                xs,
                mem,
                marker="o",
                markersize=4.5,
                linewidth=1.8,
                linestyle=style,
                color=color,
                label=label,
            )

            if 1 in runs:
                baseline = runs[1][0]
                speed = [baseline / runs[p][0] for p in xs]
                speed_ax.plot(
                    xs,
                    speed,
                    marker="o",
                    markersize=4.5,
                    linewidth=1.8,
                    linestyle=style,
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
        memory_ax.set_ylabel("Peak RSS (GiB, log10)")
        speed_ax.set_ylabel(r"Speedup ($T_1/T_p$)")
        speed_ax.set_ylim(bottom=0)

        memory_ax.set_title(
            f"{mode.upper()} — Peak Memory", fontsize=12, weight="bold", pad=12
        )
        speed_ax.set_title(
            f"{mode.upper()} — Speedup", fontsize=12, weight="bold", pad=12
        )
        for ax in (memory_ax, speed_ax):
            ax.set_xticks(THREADS, [str(p) for p in THREADS])
            ax.tick_params(
                axis="x", top=False, labeltop=False, bottom=True, labelbottom=True
            )
            ax.xaxis.set_label_position("bottom")
            ax.set_xlabel("Threads (p)", labelpad=9)
            ax.grid(True, which="major", alpha=0.25)
            ax.set_axisbelow(True)

    handles = [
        Line2D(
            [0],
            [0],
            color=(COLORS[i] if i < len(COLORS) else palette(i % 20)),
            linestyle=STYLES[i % len(STYLES)],
            marker="o",
            linewidth=1.8,
            label=label,
        )
        for i, (_key, label) in enumerate(datasets)
    ]
    handles.append(
        Line2D([0], [0], color="#777777", linestyle="--", label="Ideal linear")
    )
    fig.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.035),
        ncol=min(3, len(handles)),
        frameon=False,
        fontsize=9,
    )
    fig.subplots_adjust(hspace=0.63, wspace=0.23, top=0.88, bottom=0.07)

    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        path = output_prefix.with_suffix(f".{ext}")
        fig.savefig(path, dpi=300, bbox_inches="tight")
        print(f"Saved {path}")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path, help="Benchmark CSV input")
    parser.add_argument(
        "-o",
        "--output-prefix",
        type=Path,
        default=Path("pub_artifacts/figure_per_mode_memory_speedup"),
    )
    args = parser.parse_args()
    draw(args.csv_file, args.output_prefix)


if __name__ == "__main__":
    main()
