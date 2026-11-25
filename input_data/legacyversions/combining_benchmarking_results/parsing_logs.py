#!/usr/bin/env python3

import csv
import re
from pathlib import Path


def time_to_seconds(time_str):
    """
    Convert GNU time output to seconds.

    Examples:
        16:23.95     -> 983.95
        1:16:23.95   -> 4583.95
    """
    parts = time_str.strip().split(":")

    if len(parts) == 2:
        minutes, seconds = parts
        return int(minutes) * 60 + float(seconds)

    elif len(parts) == 3:
        hours, minutes, seconds = parts
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)

    return None


def parse_log(logfile):
    """Extract benchmark information from a log file."""

    with open(logfile, "r", errors="ignore") as f:
        text = f.read()

    result = {
        "dataset": None,
        "marker": None,
        "threads": None,
        "cpu_percent": None,
        "elapsed_seconds": None,
        "max_ram_gb": None,
        "file": str(logfile),
    }

    # Dataset name
    m = re.search(r"Dataset folder:\s+.*?/(benchmark_[^\s/]+)", text)
    if m:
        result["dataset"] = m.group(1)

    # Threads and marker
    m = re.search(
        r"Running plastburstalign with\s+(\d+)\s+threads,\s*mode:\s*(\w+)", text
    )
    if m:
        result["threads"] = int(m.group(1))
        result["marker"] = m.group(2)

    # CPU percentage
    m = re.search(r"Percent of CPU this job got:\s+(\d+)%", text)
    if m:
        result["cpu_percent"] = int(m.group(1))

    # Elapsed time
    m = re.search(
        r"Elapsed \(wall clock\) time \(h:mm:ss or m:ss\):\s+([0-9:.]+)", text
    )
    if m:
        result["elapsed_seconds"] = round(time_to_seconds(m.group(1)), 2)

    # Maximum RAM (kB -> GiB)
    m = re.search(r"Maximum resident set size \(kbytes\):\s+(\d+)", text)
    if m:
        kb = int(m.group(1))
        result["max_ram_gb"] = round(kb / (1024 * 1024), 2)

    return result


def main(log_directory, output_csv):
    rows = []

    for logfile in Path(log_directory).rglob("*"):
        if not logfile.is_file():
            continue

        try:
            with open(logfile, "r", errors="ignore") as f:
                content = f.read()

            # Only process files that look like benchmark logs
            if "Maximum resident set size" not in content:
                continue

            row = parse_log(logfile)

            # Skip incomplete records
            if (
                row["dataset"] is not None
                and row["marker"] is not None
                and row["threads"] is not None
            ):
                rows.append(row)

        except Exception as e:
            print(f"Skipping {logfile}: {e}")

    # Sort output
    rows.sort(key=lambda x: (x["dataset"], x["marker"], x["threads"]))

    with open(output_csv, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "dataset",
                "marker",
                "threads",
                "cpu_percent",
                "elapsed_seconds",
                "max_ram_gb",
                "file",
            ],
        )

        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved {len(rows)} benchmark records to {output_csv}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract runtime, CPU, RAM, and thread information from benchmark log files."
    )

    parser.add_argument("log_directory", help="Directory containing log files")

    parser.add_argument(
        "-o",
        "--output",
        default="benchmark_summary.csv",
        help="Output CSV file (default: benchmark_summary.csv)",
    )

    args = parser.parse_args()

    main(args.log_directory, args.output)
