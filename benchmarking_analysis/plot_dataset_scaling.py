import pandas as pd
import matplotlib.pyplot as plt

# ==========================
# Load data
# ==========================

df = pd.read_csv("results.csv")

marker_order = ["cds", "igs", "int"]

# ==========================
# Compute speedup
# ==========================

speedup_rows = []

for (dataset, marker), grp in df.groupby(["dataset", "marker"]):

    baseline = grp.loc[
        grp["threads"] == 1,
        "elapsed_seconds"
    ].iloc[0]

    for _, row in grp.iterrows():

        speedup_rows.append({
            "dataset": dataset,
            "marker": marker,
            "threads": row["threads"],
            "speedup": baseline / row["elapsed_seconds"]
        })

speedup_df = pd.DataFrame(speedup_rows)

# ==========================
# Create plots per dataset
# ==========================

for dataset in sorted(df["dataset"].unique()):

    clean_name = dataset.replace("benchmark_", "")

    # ------------------------------------
    # Runtime Scaling
    # ------------------------------------

    plt.figure(figsize=(8,6))

    subset = df[df["dataset"] == dataset]

    for marker in marker_order:

        d = subset[subset["marker"] == marker]

        if len(d) == 0:
            continue

        plt.plot(
            d["threads"],
            d["elapsed_seconds"],
            marker="o",
            linewidth=2,
            label=marker.upper()
        )

    plt.xscale("log", base=2)

    plt.xlabel("Threads")
    plt.ylabel("Runtime (seconds)")
    plt.title(f"{clean_name}\nRuntime Scaling")
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.tight_layout()

    plt.savefig(
        f"{clean_name}_runtime_scaling.png",
        dpi=300
    )

    plt.close()

    # ------------------------------------
    # Memory Scaling
    # ------------------------------------

    plt.figure(figsize=(8,6))

    for marker in marker_order:

        d = subset[subset["marker"] == marker]

        if len(d) == 0:
            continue

        plt.plot(
            d["threads"],
            d["max_ram_gb"],
            marker="o",
            linewidth=2,
            label=marker.upper()
        )

    plt.xscale("log", base=2)

    plt.xlabel("Threads")
    plt.ylabel("Peak RAM (GB)")
    plt.title(f"{clean_name}\nMemory Scaling")
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.tight_layout()

    plt.savefig(
        f"{clean_name}_memory_scaling.png",
        dpi=300
    )

    plt.close()

    # ------------------------------------
    # Speedup Scaling
    # ------------------------------------

    plt.figure(figsize=(8,6))

    sp = speedup_df[
        speedup_df["dataset"] == dataset
    ]

    for marker in marker_order:

        d = sp[sp["marker"] == marker]

        if len(d) == 0:
            continue

        plt.plot(
            d["threads"],
            d["speedup"],
            marker="o",
            linewidth=2,
            label=marker.upper()
        )

    # ideal scaling line
    ideal_threads = sorted(sp["threads"].unique())

    plt.plot(
        ideal_threads,
        ideal_threads,
        "--",
        linewidth=1.5,
        label="Ideal Scaling"
    )

    plt.xscale("log", base=2)

    plt.xlabel("Threads")
    plt.ylabel("Speedup")
    plt.title(f"{clean_name}\nSpeedup Scaling")
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.tight_layout()

    plt.savefig(
        f"{clean_name}_speedup_scaling.png",
        dpi=300
    )

    plt.close()


    # ------------------------------------
# CPU Utilization Scaling
# ------------------------------------

    plt.figure(figsize=(8,6))

    for marker in marker_order:

        d = subset[subset["marker"] == marker]

        if len(d) == 0:
            continue

        plt.plot(
            d["threads"],
            d["cpu_percent"],
            marker="o",
            linewidth=2,
            label=marker.upper()
        )

    # Ideal CPU utilization
    ideal_threads = sorted(subset["threads"].unique())
    ideal_cpu = [t * 100 for t in ideal_threads]

    plt.plot(
        ideal_threads,
        ideal_cpu,
        "--",
        linewidth=2,
        color="black",
        label="Ideal CPU Utilization"
    )

    plt.xscale("log", base=2)

    plt.xlabel("Threads")
    plt.ylabel("CPU Utilization (%)")
    plt.title(f"{clean_name}\nCPU Utilization Scaling")
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.tight_layout()

    plt.savefig(
        f"{clean_name}_cpu_scaling.png",
        dpi=300
    )

    plt.close()
print("All plots generated successfully.")