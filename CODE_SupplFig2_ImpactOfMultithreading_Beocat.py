#!/usr/bin/env python3
"""Plot the impact of multithreading using the Beocat benchmarks."""

from CODE_Figure5_ImpactOfMultithreading_Workstation import main as plot_multithreading


def main():
    plot_multithreading(
        default_input_csv="input_data/DATA_Benchmarking_on_Beocat__2026_11_20.csv",
        default_output_stem="VIZ_SupplFig2_ImpactOfMultithreading_Beocat/SupplFig2_ImpactOfMultithreading_Beocat",
    )


if __name__ == "__main__":
    main()
