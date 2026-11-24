#!/bin/bash
#SBATCH --job-name=pba_pub_sweep
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --partition=killable.q,batch.q
#SBATCH --requeue
#SBATCH --constraint=warlocks
#SBATCH --nodelist=warlock[35-37]
#SBATCH --array=0-89%6
#SBATCH --output=logs_pub/sweep_%A_%a.out
#SBATCH --error=logs_pub/sweep_%A_%a.err

set -euo pipefail
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1

mkdir -p logs_pub results_pub_sweep final_csv_pub

datasets=(
    "benchmark_ZhangNNEtAl2025_53angiosperms"
    "benchmark_YangEtAl2022_Asteraceae"
    "benchmark_YangEtAl2022_angiosperms"
    "benchmark_YangEtAl2022_monocots"
    "benchmark_ZhangNNEtAl2025_13724angiosperms"
)
thread_counts=(1 2 4 8 16 32)
modes=("cds" "int" "igs")

total_combinations=$((${#thread_counts[@]} * ${#modes[@]}))
i=$((SLURM_ARRAY_TASK_ID / total_combinations))
j=$(((SLURM_ARRAY_TASK_ID / ${#modes[@]}) % ${#thread_counts[@]}))
k=$((SLURM_ARRAY_TASK_ID % ${#modes[@]}))

dataset="${datasets[$i]}"
threads="${thread_counts[$j]}"
mode="${modes[$k]}"

DATA_DIR=""
for cand in "benchmarking/$dataset" "$dataset" "../$dataset" "/bulk/$USER/$dataset"; do
    if [ -d "$cand" ]; then
        DATA_DIR="$cand"
        break
    fi
done

if [ -z "$DATA_DIR" ]; then
    echo "Dataset $dataset not found, skipping."
    exit 1
fi

OUT_DIR="results_pub_sweep/${dataset}_output_${mode}_${threads}threads"
rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"
STAT_OUT="results_pub_sweep/stat_${dataset}_${threads}_${mode}.txt"

echo "=== [PUB SWEEP] Task ${SLURM_ARRAY_TASK_ID}: $dataset | $mode | $threads threads on $(hostname) ==="

/usr/bin/time -v -o "$STAT_OUT" \
    python3 -m plastburstalign \
        -i "$DATA_DIR" \
        -o "$OUT_DIR" \
        -s "$mode" \
        -n "$threads"

python3 - "$dataset" "$threads" "$mode" "$STAT_OUT" "$SLURM_ARRAY_TASK_ID" << 'PYEOF'
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
