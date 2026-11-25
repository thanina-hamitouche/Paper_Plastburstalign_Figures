import argparse
from datetime import date
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter, LogLocator

CONFIG_ORDER = ["16*1", "8*2", "4*4", "2*8", "1*16"]

CONFIG_LABELS = {
    "16*1": "16 × 1",
    "8*2": "8 × 2",
    "4*4": "4 × 4",
    "2*8": "2 × 8",
    "1*16": "1 × 16",
}

COLORS = {
    "time": "#377eb8",
    "memory": "#e41a1c",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plot execution time and memory usage across parallelism configurations."
    )
    parser.add_argument(
        "input_csv",
        nargs="?",
        default="./benchmark_summary.csv",
        help="Input benchmark CSV file.",
    )
    parser.add_argument(
        "output_path_stem",
        nargs="?",
        default="./VIZ_Parallelism/PlastBurstAlign_Parallelism",
        help="Output path stem; writes .png, .svg, and .pdf files.",
    )
    return parser.parse_args()


def ensure_output_dir(output_stem: Path) -> None:
    output_stem.parent.mkdir(parents=True, exist_ok=True)


def format_axis(ax: plt.Axes, ylabel: str) -> None:
    ax.set_xticks(range(len(CONFIG_ORDER)))
    ax.set_xticklabels(
        [CONFIG_LABELS[c] for c in CONFIG_ORDER],
        fontsize=11,
    )

    ax.set_xlabel(
        "MAFFT × Workers threads per alignment\n(16-CPU budget)",
        fontsize=12,
    )
    ax.set_ylabel(ylabel, fontsize=12)

    ax.grid(
        True,
        which="major",
        color="gray",
        alpha=0.45,
        linewidth=0.8,
    )
    ax.grid(False, which="minor")
    ax.set_axisbelow(True)


def main() -> None:
    args = parse_args()

    input_csv = Path(args.input_csv)
    output_stem = Path(args.output_path_stem)
    output_stem = output_stem.with_name(f"{output_stem.stem}__{date.today():%Y_%m_%d}")

    if not input_csv.exists():
        raise FileNotFoundError(f"Input file does not exist: {input_csv}")

    ensure_output_dir(output_stem)

    # ==========================================
    # 1. Load benchmark data
    # ==========================================

    plot_df = pd.read_csv(input_csv)

    required_columns = {"Config", "Elapsed", "MaxRSS_KB"}
    missing = required_columns - set(plot_df.columns)

    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    plot_df["Config"] = (
        plot_df["Config"]
        .astype(str)
        .str.strip()
        .str.replace("×", "*", regex=False)
        .str.replace(" ", "", regex=False)
    )

    plot_df = plot_df[plot_df["Config"].isin(CONFIG_ORDER)].copy()

    plot_df["Config"] = pd.Categorical(
        plot_df["Config"],
        categories=CONFIG_ORDER,
        ordered=True,
    )

    plot_df["Elapsed"] = pd.to_numeric(plot_df["Elapsed"], errors="coerce")
    plot_df["MaxRSS_KB"] = pd.to_numeric(plot_df["MaxRSS_KB"], errors="coerce")

    plot_df.dropna(
        subset=["Config", "Elapsed", "MaxRSS_KB"],
        inplace=True,
    )

    if plot_df.empty:
        raise ValueError("No valid benchmark records found.")

    # Average repeated runs if present.
    plot_df = (
        plot_df.groupby("Config", observed=True)
        .agg(
            Elapsed=("Elapsed", "mean"),
            MaxRSS_KB=("MaxRSS_KB", "mean"),
        )
        .reindex(CONFIG_ORDER)
        .dropna()
        .reset_index()
    )

    x = np.array(
        [CONFIG_ORDER.index(config) for config in plot_df["Config"].astype(str)]
    )

    # ==========================================
    # 2. Figure configuration
    # ==========================================

    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = [
        "Arial",
        "Liberation Sans",
        "DejaVu Sans",
        "sans-serif",
    ]

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(15, 6),
    )

    # ==========================================
    # 3. Execution time (LINEAR scale)
    # ==========================================

    ax = axes[0]

    ax.plot(
        x,
        plot_df["Elapsed"],
        color=COLORS["time"],
        linestyle="solid",
        linewidth=2.5,
        marker="o",
        markersize=7,
        label="Elapsed time",
    )

    ax.set_yscale("linear")  # NOT log10
    min_time = plot_df["Elapsed"].min()
    max_time = plot_df["Elapsed"].max()

    margin = (max_time - min_time) * 0.2

    ax.set_ylim(min_time - margin, max_time + margin)

    for xi, value in zip(x, plot_df["Elapsed"]):
        ax.annotate(
            f"{value:.2f} s",
            (xi, value),
            xytext=(0, 11),
            textcoords="offset points",
            ha="center",
            fontsize=10,
        )

    format_axis(ax, "Elapsed time (seconds)")
    ax.set_title("Execution time", fontsize=15, pad=15)
    ax.legend(loc="upper right")

    # ==========================================
    # 4. Peak memory usage (log10 scale)
    # ==========================================

    ax = axes[1]

    memory = plot_df["MaxRSS_KB"]

    if (memory <= 0).any():
        raise ValueError("Memory values must be positive for log10 scaling.")

    ax.plot(
        x,
        memory,
        color=COLORS["memory"],
        linestyle="solid",
        linewidth=2.5,
        marker="o",
        markersize=7,
        label="Peak memory",
    )

    for xi, value in zip(x, memory):
        ax.annotate(
            f"{value / 1024:.1f} MiB",
            (xi, value),
            xytext=(0, 11),
            textcoords="offset points",
            ha="center",
            fontsize=10,
            color="0.2",
            bbox={
                "boxstyle": "round,pad=0.2",
                "fc": (1, 1, 1, 0.65),
                "ec": "none",
            },
        )

    ax.set_yscale("log", base=10)

    ax.yaxis.set_major_locator(LogLocator(base=10, subs=(1.0,)))

    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, pos: f"{value:,.0f}"))

    ax.set_ylim(
        memory.min() / 1.5,
        memory.max() * 1.6,
    )

    format_axis(ax, "Maximum RSS (KB, log10 scale)")

    ax.set_title(
        "Peak memory usage",
        fontsize=15,
        pad=15,
    )

    ax.legend(loc="upper right", frameon=True)

    # ==========================================
    # 5. Overall figure formatting
    # ==========================================

    fig.tight_layout()

    # ==========================================
    # 6. Export figures
    # ==========================================

    fig.savefig(
        output_stem.with_suffix(".svg"),
        bbox_inches="tight",
    )

    fig.savefig(
        output_stem.with_suffix(".png"),
        dpi=300,
        bbox_inches="tight",
    )
    fig.savefig(
        output_stem.with_suffix(".pdf"),
        bbox_inches="tight",
    )

    plt.show()
    plt.close(fig)


if __name__ == "__main__":
    main()
