import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# =========================
# Load data
# =========================

df = pd.read_csv("results.csv")

# Consistent ordering
marker_order = ["cds", "igs", "int"]

datasets = [
    "benchmark_YangEtAl2022_Asteraceae",
    "benchmark_YangEtAl2022_monocots",
    "benchmark_YangEtAl2022_angiosperms",
    "benchmark_ZhangNNEtAl2025_53angiosperms",
    "benchmark_ZhangNNEtAl2025_13724angiosperms"
]

# =========================
# Figure 1
# Runtime scaling
# =========================

for marker in marker_order:

    plt.figure(figsize=(8,6))

    sub = df[df["marker"] == marker]

    for dataset in sub["dataset"].unique():

        d = sub[sub["dataset"] == dataset]
        plt.plot(
            d["threads"],
            d["elapsed_seconds"],
            marker="o",
            label=dataset.replace("benchmark_","")
        )

    plt.xscale("log", base=2)

    plt.xlabel("Threads")
    plt.ylabel("Runtime (seconds)")
    plt.title(f"Runtime Scaling ({marker.upper()})")
    plt.legend(fontsize=8)
    plt.tight_layout()

    plt.savefig(f"runtime_scaling_{marker}.png", dpi=300)

# =========================
# Figure 2
# Speedup
# =========================

speedup_df = []

for (dataset, marker), grp in df.groupby(["dataset","marker"]):

    baseline = grp.loc[grp["threads"] == 1, "elapsed_seconds"].iloc[0]

    for _, row in grp.iterrows():

        speedup = baseline / row["elapsed_seconds"]

        speedup_df.append([
            dataset,
            marker,
            row["threads"],
            speedup
        ])

speedup_df = pd.DataFrame(
    speedup_df,
    columns=["dataset","marker","threads","speedup"]
)

for marker in marker_order:

    plt.figure(figsize=(8,6))

    sub = speedup_df[speedup_df["marker"] == marker]

    for dataset in sub["dataset"].unique():

        d = sub[sub["dataset"] == dataset]

        plt.plot(
            d["threads"],
            d["speedup"],
            marker="o",
            label=dataset.replace("benchmark_","")
        )

    plt.plot(
        [1,2,4,8,16,32],
        [1,2,4,8,16,32],
        "--",
        label="Ideal"
    )

    plt.xscale("log", base=2)

    plt.xlabel("Threads")
    plt.ylabel("Speedup")
    plt.title(f"Speedup ({marker.upper()})")
    plt.legend(fontsize=8)

    plt.tight_layout()

    plt.savefig(f"speedup_{marker}.png", dpi=300)

# =========================
# Figure 3
# Parallel efficiency
# =========================

eff_df = speedup_df.copy()
eff_df["efficiency"] = eff_df["speedup"] / eff_df["threads"]

for marker in marker_order:

    plt.figure(figsize=(8,6))

    sub = eff_df[eff_df["marker"] == marker]

    for dataset in sub["dataset"].unique():

        d = sub[sub["dataset"] == dataset]

        plt.plot(
            d["threads"],
            d["efficiency"] * 100,
            marker="o",
            label=dataset.replace("benchmark_","")
        )

    plt.xscale("log", base=2)

    plt.xlabel("Threads")
    plt.ylabel("Efficiency (%)")
    plt.title(f"Parallel Efficiency ({marker.upper()})")
    plt.legend(fontsize=8)

    plt.tight_layout()

    plt.savefig(f"efficiency_{marker}.png", dpi=300)

# =========================
# Figure 4
# RAM scaling
# =========================

for marker in marker_order:

    plt.figure(figsize=(8,6))

    sub = df[df["marker"] == marker]

    for dataset in sub["dataset"].unique():

        d = sub[sub["dataset"] == dataset]

        plt.plot(
            d["threads"],
            d["max_ram_gb"],
            marker="o",
            label=dataset.replace("benchmark_","")
        )

    plt.xscale("log", base=2)

    plt.xlabel("Threads")
    plt.ylabel("Peak RAM (GB)")
    plt.title(f"Memory Scaling ({marker.upper()})")
    plt.legend(fontsize=8)

    plt.tight_layout()

    plt.savefig(f"memory_scaling_{marker}.png", dpi=300)

# =========================
# Figure 5
# CPU utilization
# =========================

plt.figure(figsize=(10,6))

for marker in marker_order:

    sub = (
        df.groupby(["marker","threads"])
        ["cpu_percent"]
        .mean()
        .reset_index()
    )

    d = sub[sub["marker"] == marker]

    plt.plot(
        d["threads"],
        d["cpu_percent"],
        marker="o",
        label=marker.upper()
    )

plt.xscale("log", base=2)

plt.xlabel("Threads")
plt.ylabel("CPU Utilization (%)")
plt.title("Average CPU Utilization")
plt.legend()

plt.tight_layout()

plt.savefig("cpu_utilization.png", dpi=300)

# =========================
# Figure 6
# Marker comparison
# Runtime at 1 thread
# =========================

single = df[df["threads"] == 1]

pivot = single.pivot(
    index="dataset",
    columns="marker",
    values="elapsed_seconds"
)

pivot.plot(
    kind="bar",
    figsize=(10,6)
)

plt.ylabel("Runtime (seconds)")
plt.title("Marker Runtime Comparison (1 Thread)")
plt.tight_layout()

plt.savefig("marker_runtime_comparison.png", dpi=300)

# =========================
# Figure 7
# Marker comparison
# RAM at 1 thread
# =========================

pivot = single.pivot(
    index="dataset",
    columns="marker",
    values="max_ram_gb"
)

pivot.plot(
    kind="bar",
    figsize=(10,6)
)

plt.ylabel("Peak RAM (GB)")
plt.title("Marker Memory Comparison (1 Thread)")
plt.tight_layout()

plt.savefig("marker_memory_comparison.png", dpi=300)

print("All figures generated.")
