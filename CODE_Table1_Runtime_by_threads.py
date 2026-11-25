#!/usr/bin/env python3
"""Generate publication Markdown and LaTeX tables from benchmark CSV files."""

import argparse
import csv
from collections import defaultdict
from pathlib import Path

DATASET_ORDER = [
    ("benchmark_ZhangNNEtAl2025_53angiosperms", "Zhang et al. (53 angiosperms)"),
    ("benchmark_YangEtAl2022_Asteraceae", "Yang et al. (Asteraceae)"),
    ("benchmark_YangEtAl2022_monocots", "Yang et al. (Monocots)"),
    ("benchmark_YangEtAl2022_angiosperms", "Yang et al. (Angiosperms)"),
    ("benchmark_ZhangNNEtAl2025_13724angiosperms", "Zhang et al. (13,724 angiosperms)"),
]
MODES = ["cds", "int", "igs"]


def load_csv(path: Path, required: bool = False) -> dict:
    data = defaultdict(dict)
    if not path.is_file():
        if required:
            raise FileNotFoundError(f"CSV file not found: {path}")
        return data
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


def parse_elapsed(s: str) -> float:
    parts = [float(x) for x in s.strip().split(":")]
    return (
        parts[0] * 3600 + parts[1] * 60 + parts[2]
        if len(parts) == 3
        else parts[0] * 60 + parts[1]
    )


def fmt_dur(sec: float) -> str:
    if sec >= 3600:
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = int(round(sec % 60))
        return f"{h}h {m:02d}m {s:02d}s"
    if sec >= 60:
        m = int(sec // 60)
        s = sec - 60 * m
        return f"{m}m {s:04.1f}s"
    return f"{sec:.1f}s"


def make_tables(
    publication_csv: Path,
    baseline_csv: Path,
    out_dir: Path,
    output_name: str = "table_strong_scaling",
) -> None:
    pub = load_csv(publication_csv, required=True)
    base = load_csv(baseline_csv)
    out_dir.mkdir(parents=True, exist_ok=True)

    md_lines = [
        "| Dataset | Mode | 1t Wall | 16t Wall ($S_{16}$) | 32t Wall ($S_{32}$, $E_{32}$) | 32t Peak RSS | vs. Pre-Patch 32t |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    tex_lines = [
        r"\begin{tabular}{llrrrrr}",
        r"\toprule",
        r"Dataset & Mode & $T_1$ (s) & $T_{16}$ (s) & $T_{32}$ (s) & Speedup $S_{32}$ ($E_{32}$) & Peak RSS (GiB) \\",
        r"\midrule",
    ]

    for ds_key, ds_label in DATASET_ORDER:
        added = False
        for mode in MODES:
            runs = pub.get((ds_key, mode), {})
            if not runs:
                continue
            added = True
            t1 = parse_elapsed(runs[1]["Elapsed"]) if 1 in runs else None
            t16 = parse_elapsed(runs[16]["Elapsed"]) if 16 in runs else None
            t32 = parse_elapsed(runs[32]["Elapsed"]) if 32 in runs else None
            rss32 = int(runs[32]["MaxRSS_KB"]) / 1048576 if 32 in runs else None

            t1_md = fmt_dur(t1) if t1 is not None else "-"
            t16_md = fmt_dur(t16) if t16 is not None else "-"
            if t1 is not None and t16 is not None and t16 > 0:
                t16_md += f" ({t1 / t16:.2f}x)"

            t32_md = fmt_dur(t32) if t32 is not None else "-"
            s32_tex = "-"
            if t1 is not None and t32 is not None and t32 > 0:
                speedup = t1 / t32
                efficiency = speedup / 32 * 100
                t32_md = f"**{fmt_dur(t32)}** (**{speedup:.2f}x**, {efficiency:.1f}%)"
                s32_tex = f"{speedup:.2f}$\\times$ ({efficiency:.1f}\\%)"

            baseline = base.get((ds_key, mode), {})
            gain_md = "-"
            if 32 in baseline and t32 is not None and t32 > 0:
                gain_md = f"{parse_elapsed(baseline[32]['Elapsed']) / t32:.2f}x faster"

            rss_md = f"{rss32:.2f} GiB" if rss32 is not None else "-"
            rss_tex = f"{rss32:.2f}" if rss32 is not None else "-"
            md_lines.append(
                f"| {ds_label} | `{mode.upper()}` | {t1_md} | {t16_md} | "
                f"{t32_md} | {rss_md} | {gain_md} |"
            )
            tex_lines.append(
                f"{ds_label} & {mode.upper()} & "
                f"{f'{t1:.1f}' if t1 is not None else '-'} & "
                f"{f'{t16:.1f}' if t16 is not None else '-'} & "
                f"{f'{t32:.1f}' if t32 is not None else '-'} & "
                f"{s32_tex} & {rss_tex} \\\\"
            )
        if added:
            tex_lines.append(r"\addlinespace")

    if tex_lines[-1] == r"\addlinespace":
        tex_lines.pop()
    tex_lines += [r"\bottomrule", r"\end{tabular}"]

    md_path = out_dir / f"{output_name}.md"
    tex_path = out_dir / f"{output_name}.tex"
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    tex_path.write_text("\n".join(tex_lines) + "\n", encoding="utf-8")
    print(f"Wrote {md_path} and {tex_path}")
    # if not baseline_csv.is_file():
    #     print(f"Note: no baseline CSV at {baseline_csv}; pre-patch comparison is '-'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-csv",
        "--pub-csv",
        type=Path,
        default=Path("publication_summary_metrics.csv"),
    )
    parser.add_argument(
        "--base-csv", type=Path, default=Path("baseline_summary_metrics.csv")
    )
    output_options = parser.add_mutually_exclusive_group()
    output_options.add_argument(
        "--out-dir", type=Path, help="Output directory using the default filename."
    )
    output_options.add_argument(
        "--output-prefix",
        type=Path,
        help="Output path with or without extension; writes Markdown and LaTeX.",
    )
    args = parser.parse_args()
    if args.output_prefix is None:
        make_tables(
            args.input_csv,
            args.base_csv,
            args.out_dir or Path("TBL_Table1_Runtime_by_threads"),
        )
    else:
        if not args.output_prefix.name:
            parser.error("--output-prefix must include a filename")
        make_tables(
            args.input_csv, args.base_csv, args.output_prefix.parent, args.output_prefix.stem
        )


# python CODE_Table1_Runtime_by_threads.py --input-csv input_data/DATA_Benchmarking_on_Workstation__2026_11_24.csv
