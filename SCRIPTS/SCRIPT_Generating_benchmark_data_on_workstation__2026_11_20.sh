#!/usr/bin/env bash
# Standalone workstation equivalent of submit_nina_publication_sweep.slurm
# Runs sequentially (one benchmark at a time) to avoid CPU contention on a single machine.
# Optional usage:
#   ./run_benchmark_sweep_workstation.sh                       # full 90-run sweep
#   DATASETS="benchmark_ZhangNNEtAl2025_53angiosperms" ./run_benchmark_sweep_workstation.sh

set -euo pipefail
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1

mkdir -p logs_pub results_pub_sweep final_csv_pub

if [ -n "${DATASETS:-}" ]; then
    read -r -a datasets <<< "$DATASETS"
else
    datasets=(
        "benchmark_ZhangNNEtAl2025_53angiosperms"
        "benchmark_YangEtAl2022_Asteraceae"
        "benchmark_YangEtAl2022_angiosperms"
        "benchmark_YangEtAl2022_monocots"
        "benchmark_ZhangNNEtAl2025_13724angiosperms"
    )
fi

thread_counts=(${THREADS_LIST:-1 2 4 8 16 32})
modes=(${MODES_LIST:-cds int igs})

tid=0
for dataset in "${datasets[@]}"; do
    DATA_DIR=""
    for cand in "benchmarking/$dataset" "$dataset" "../$dataset"; do
        if [ -d "$cand" ]; then
            DATA_DIR="$cand"
            break
        fi
    done
    if [ -z "$DATA_DIR" ]; then
        echo "[WARN] Dataset $dataset not found, skipping."
        tid=$((tid + ${#thread_counts[@]} * ${#modes[@]}))
        continue
    fi

    for threads in "${thread_counts[@]}"; do
        for mode in "${modes[@]}"; do
            OUT_DIR="results_pub_sweep/${dataset}_output_${mode}_${threads}threads"
            STAT_OUT="results_pub_sweep/stat_${dataset}_${threads}_${mode}.txt"
            LOG_OUT="logs_pub/run_${tid}_${dataset}_${mode}_${threads}t.log"
            rm -rf "$OUT_DIR"
            mkdir -p "$OUT_DIR"

            echo "=== [Task $tid] $dataset | $mode | $threads threads ==="
            /usr/bin/time -v -o "$STAT_OUT" \
                python3 -m plastburstalign \
                    -i "$DATA_DIR" \
                    -o "$OUT_DIR" \
                    -s "$mode" \
                    -n "$threads" \
                > "$LOG_OUT" 2>&1

            python3 - "$dataset" "$threads" "$mode" "$STAT_OUT" "$tid" << 'PYEOF'
import re, sys
from pathlib import Path

dataset, threads, mode, stat_path, tid = sys.argv[1:6]
txt = Path(stat_path).read_text()

def grab(pattern, default="0"):
    m = re.search(pattern, txt)
    return m.group(1).strip() if m else default

row = ",".join([
    dataset,
    threads,
    mode,
    grab(r"User time \(seconds\):\s*([0-9.]+)"),
    grab(r"System time \(seconds\):\s*([0-9.]+)"),
    grab(r"Elapsed \(wall clock\) time \(h:mm:ss or m:ss\):\s*([0-9:.]+)"),
    grab(r"Percent of CPU this job got:\s*([0-9]+%)"),
    grab(r"Maximum resident set size \(kbytes\):\s*([0-9]+)"),
    grab(r"Major \(requiring I/O\) page faults:\s*([0-9]+)"),
    grab(r"Minor \(reclaiming a frame\) page faults:\s*([0-9]+)"),
]) + "\n"

Path(f"final_csv_pub/row_{tid}.csv").write_text(row)
PYEOF
            tid=$((tid + 1))
        done
    done
done

echo "=== Sweep finished; aggregating final_csv_pub/ ==="
python3 audit_pub_sweep.py
