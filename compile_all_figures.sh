#!/usr/bin/env bash
set -e

compiled_dir="./_COMPILED_FIGURES_"
mkdir -p "$compiled_dir"

run_figure() {
  local prefix="$1" start_date end_date output_date ext
  shift
  start_date="$(date +%Y_%m_%d)"
  "$@" --output-prefix "$prefix"
  end_date="$(date +%Y_%m_%d)"
  output_date="$end_date"
  if [ "$start_date" != "$end_date" ] && [ ! -f "${prefix}__${end_date}.png" ]; then
    output_date="$start_date"
  fi
  for ext in png svg pdf; do
    if [ ! -f "${prefix}__${output_date}.${ext}" ]; then
      echo "Missing generated figure: ${prefix}__${output_date}.${ext}" >&2
      return 1
    fi
  done
  for ext in png svg pdf; do
    cp "${prefix}__${output_date}.${ext}" "$compiled_dir/"
  done
}

# Figure 1
echo "Compiling figure 1 ..."
run_figure "./VIZ_Figure1_AccumulationGraph/Figure1_AccumulationGraph_recordsAndPublications" \
  Rscript "CODE_Figure1_AccumulationGraph.R" \
  --input-records "./input_data/DATA_Compilation_of_all_plastid_genomes__2026_06_01.tsv" \
  --input-csv "./input_data/DATA_Compilation_of_plastome_publications__2026_10_25.csv" \
  --start-date "2016-01-01" \
  --end-date "2025-12-31"
echo ""

# Figure 2
echo "Compiling figure 2 ..."
run_figure "./VIZ_Figure2_MethodOverview/Figure2_MethodOverview" \
  python CODE_Figure2_MethodOverview.py
echo ""

# Figure 3
echo "Compiling figure 3 ..."
run_figure "./VIZ_Figure3_OverviewWorkflow/Figure3_WorkflowOverview" \
  python CODE_Figure3_OverviewWorkflow.py
echo ""

# Figure 4
echo "Compiling figure 4 ..."
run_figure "./VIZ_Figure4_Speedup_and_Wallclocktime/Figure4_Speedup_and_Wallclocktime" \
  python CODE_Figure4_Speedup_and_Wallclocktime.py \
  --input-csv ./input_data/DATA_Benchmarking_on_Workstation__2026_11_24.csv
echo ""

# Figure 5
echo "Compiling figure 5 ..."
run_figure "./VIZ_Figure5_Differences_across_datasets/Figure5_Differences_across_datasets" \
  python CODE_Figure5_Differences_across_datasets.py \
  --input-csv ./input_data/DATA_Benchmarking_on_Workstation__2026_11_24.csv
echo ""

# Suppl. Figure 1
echo "Compiling supplemental figure 1 ..."
run_figure "./VIZ_SupplFig1_ParallelismTypes_Asteraceae_CDS/SupplFig1_ParallelismTypes_Asteraceae_CDS" \
  python CODE_SupplFig1_ParallelismTypes_Asteraceae_CDS.py \
  --input-csv ./input_data/DATA_ParallelismTypes_Asteraceae_CDS__2026_11_23.csv
echo ""

# Suppl. Figure 2
echo "Compiling supplemental figure 2 ..."
run_figure "./VIZ_SupplFig2_Effectiveness_Multithreading/SupplFig2_Effectiveness_Multithreading" \
  python CODE_SupplFig2_Effectiveness_Multithreading.py \
  --input-csv ./input_data/DATA_Benchmarking_on_Workstation__2026_11_24.csv
echo ""

# Suppl. Figure 3
echo "Compiling supplemental figure 3 ..."
run_figure "./VIZ_SupplFig3_peakMem_speedup/peakMem_speedup_across_datasets" \
  python CODE_SupplFig3_peakMem_speedup.py \
  --input-csv ./input_data/DATA_Benchmarking_on_Workstation__2026_11_24.csv
echo ""

echo "Copied figures to $compiled_dir"
