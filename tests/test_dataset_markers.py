import sys
import tempfile
import unittest
from collections import Counter
from importlib import import_module
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from PIL import Image

import CODE_SupplFig1_Benchmarking_Workstation__by_extraction_mode as workstation
import CODE_SupplFig2_ImpactOfMultithreading_Beocat as suppl2_beocat
import CODE_Figure5_ImpactOfMultithreading_Workstation as figure5
import CODE_Figure4_Benchmarking_Workstation__by_dataset as by_dataset
from figure_export_helper import TYPOGRAPHY


suppl1 = import_module("CODE-FUTURE_ParallelismTypes_Asteraceae_CDS")
INPUT = Path(__file__).resolve().parents[1] / "input_data" / "DATA_Benchmarking_on_Workstation__2026_11_24.csv"
BEOCAT_INPUT = Path(__file__).resolve().parents[1] / "input_data" / "DATA_Benchmarking_on_Beocat__2026_11_20.csv"
SUPPL1_INPUT = Path(__file__).resolve().parents[1] / "input_data" / "DATA_ParallelismTypes_Asteraceae_CDS__2026_11_23.csv"
EXPECTED = {
    "#377eb8": "o",
    "#4daf4a": "s",
    "#984ea3": "^",
    "#ff7f00": "D",
    "#e41a1c": "v",
}


class DatasetMarkerTests(unittest.TestCase):
    def test_supplemental_figure2_uses_beocat_data(self):
        with patch.object(Figure, "savefig") as savefig, patch.object(plt, "close"), \
             patch.object(Path, "mkdir"), patch.object(sys, "argv", ["figure"]):
            suppl2_beocat.main()
            fig = plt.gcf()
        self.addCleanup(plt.close, fig)
        expected = Counter(
            (thread, round(elapsed / 60, 8))
            for runs in workstation.load_metrics(BEOCAT_INPUT).values()
            for thread, (elapsed, _) in runs.items()
        )
        self.assertEqual(
            Counter((int(label.xy[0]), round(label.xy[1], 8)) for label in fig.axes[0].texts),
            expected,
        )
        self.assert_dataset_styles(fig, set(EXPECTED))
        labels = fig.axes[0].texts
        for dpi in (100, 300):
            with self.subTest(dpi=dpi):
                fig.set_dpi(dpi)
                fig.canvas.draw()
                renderer = fig.canvas.get_renderer()
                bounds = [label.get_bbox_patch().get_window_extent(renderer) for label in labels]
                for index, left in enumerate(bounds):
                    for right in bounds[index + 1:]:
                        self.assertFalse(left.overlaps(right))
                for thread in {label.xy[0] for label in labels}:
                    group = sorted(
                        (label for label in labels if label.xy[0] == thread),
                        key=lambda label: label.xy[1],
                    )
                    for lower, upper in zip(group, group[1:]):
                        self.assertLessEqual(
                            lower.get_bbox_patch().get_window_extent(renderer).y1,
                            upper.get_bbox_patch().get_window_extent(renderer).y0,
                        )
        outputs = [call.args[0] for call in savefig.call_args_list]
        self.assertEqual({output.suffix for output in outputs}, {".png", ".svg", ".pdf"})
        self.assertTrue(all(
            output.parent == Path("VIZ_SupplFig2_ImpactOfMultithreading_Beocat")
            and output.name.startswith("SupplFig2_ImpactOfMultithreading_Beocat__")
            for output in outputs
        ))

    def test_figure5_default_output_prefix(self):
        with patch.object(sys, "argv", ["figure"]):
            args = figure5.parse_args()
        self.assertEqual(
            Path(args.output_path_stem),
            Path("VIZ_Figure5_ImpactOfMultithreading_Workstation")
            / "Figure5_ImpactOfMultithreading_Workstation",
        )

    def test_figure5_title_and_vertical_margins(self):
        with patch.object(Figure, "savefig") as savefig, patch.object(plt, "close"), \
             patch.object(sys, "argv", ["figure", "--input-csv", str(INPUT)]):
            figure5.main()
            fig = plt.gcf()
        self.addCleanup(plt.close, fig)
        self.assertIsNone(fig._suptitle)
        self.assertEqual(fig.axes[0].get_xlabel(), "\nThreads (log2)")
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        ax = fig.axes[0]
        x_ticks = [tick.get_window_extent(renderer) for tick in ax.get_xticklabels() if tick.get_visible() and tick.get_text()]
        y_ticks = [tick.get_window_extent(renderer) for tick in ax.get_yticklabels() if tick.get_visible() and tick.get_text()]
        x_gap = (min(tick.y0 for tick in x_ticks) - ax.xaxis.label.get_window_extent(renderer).y1) * 72 / fig.dpi
        y_gap = (min(tick.x0 for tick in y_ticks) - ax.yaxis.label.get_window_extent(renderer).x1) * 72 / fig.dpi
        self.assertAlmostEqual(x_gap, 2)
        self.assertAlmostEqual(y_gap, 2)
        content = fig.get_tightbbox(renderer)
        export = savefig.call_args.kwargs["bbox_inches"]
        for margin in (content.y0 - export.y0, export.y1 - content.y1):
            self.assertGreaterEqual(margin, 0)
            self.assertLess(margin, 0.1)

    def test_figure5_duration_labels_are_ordered_and_separated(self):
        with patch.object(Figure, "savefig") as savefig, patch.object(plt, "close"), \
             patch.object(sys, "argv", ["figure", "--input-csv", str(INPUT)]):
            figure5.main()
            fig = plt.gcf()
        self.addCleanup(plt.close, fig)
        ax = fig.axes[0]
        labels = ax.texts
        expected = Counter(
            (thread, round(elapsed / 60, 8))
            for runs in workstation.load_metrics(INPUT).values()
            for thread, (elapsed, _) in runs.items()
        )
        self.assertEqual(
            Counter((int(label.xy[0]), round(label.xy[1], 8)) for label in labels),
            expected,
        )
        export = savefig.call_args.kwargs["bbox_inches"]
        for dpi in (100, 300):
            with self.subTest(dpi=dpi):
                fig.set_dpi(dpi)
                fig.canvas.draw()
                renderer = fig.canvas.get_renderer()
                bounds = [label.get_bbox_patch().get_window_extent(renderer) for label in labels]
                for index, left in enumerate(bounds):
                    for right in bounds[index + 1:]:
                        self.assertFalse(left.overlaps(right))
                for thread in {label.xy[0] for label in labels}:
                    group = sorted(
                        (label for label in labels if label.xy[0] == thread),
                        key=lambda label: label.xy[1],
                    )
                    for lower, upper in zip(group, group[1:]):
                        self.assertLessEqual(
                            lower.get_bbox_patch().get_window_extent(renderer).y1,
                            upper.get_bbox_patch().get_window_extent(renderer).y0,
                        )
                for bounds_ in bounds:
                    self.assertGreaterEqual(bounds_.y0, ax.get_window_extent(renderer).y0 - dpi / 1000)
                    self.assertLessEqual(bounds_.y1, ax.get_window_extent(renderer).y1 + dpi / 1000)
                    self.assertGreaterEqual(bounds_.x0 / dpi, export.x0)
                    self.assertLessEqual(bounds_.x1 / dpi, export.x1)

    def test_figure5_reports_when_labels_cannot_fit(self):
        fig, ax = plt.subplots(figsize=(2, 2))
        self.addCleanup(plt.close, fig)
        labels = [
            ax.annotate(
                str(index), xy=(0.5, 0.5), xytext=(5, 0),
                textcoords="offset points", va="center", bbox={"boxstyle": "round,pad=0.2"},
            )
            for index in range(30)
        ]
        with self.assertRaisesRegex(ValueError, "Too many duration labels"):
            figure5.stack_duration_labels(ax, labels)

    def test_figure5_reports_overlapping_thread_columns(self):
        fig, ax = plt.subplots(figsize=(2, 2))
        self.addCleanup(plt.close, fig)
        labels = [
            ax.annotate(
                "Duration", xy=(thread, 0.5), xytext=(5, 0),
                textcoords="offset points", va="center", bbox={"boxstyle": "round,pad=0.2"},
            )
            for thread in (0.5, 0.501)
        ]
        with self.assertRaisesRegex(ValueError, "overlap across thread counts"):
            figure5.stack_duration_labels(ax, labels)

    def assert_chart_font_sizes(self, fig, increase=0):
        for ax in fig.axes:
            for label in (ax.xaxis.label, ax.yaxis.label):
                if label.get_text():
                    self.assertEqual(label.get_fontsize(), TYPOGRAPHY["axis_label_size"] + increase)
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                if label.get_visible() and label.get_text():
                    self.assertEqual(label.get_fontsize(), TYPOGRAPHY["tick_label_size"] + increase)
            if ax.get_title():
                self.assertEqual(ax.title.get_fontsize(), TYPOGRAPHY["title_size"] + increase)
        if fig._supxlabel is not None:
            self.assertEqual(fig._supxlabel.get_fontsize(), TYPOGRAPHY["axis_label_size"] + increase)

    def assert_legend_layout(self, fig, label_gap=8, legend_gap=16, increase=0):
        self.assertEqual(len(fig.legends), 1)
        legend = fig.legends[0]
        self.assertTrue(all(
            text.get_fontsize() == TYPOGRAPHY["legend_size"] + increase
            for text in legend.get_texts()
        ))
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        bottom = min(ax.get_tightbbox(renderer).y0 for ax in fig.axes if ax.get_visible())
        if fig._supxlabel is not None and fig._supxlabel.get_visible():
            xlabel_bbox = fig._supxlabel.get_window_extent(renderer)
            if label_gap is not None:
                self.assertAlmostEqual((bottom - xlabel_bbox.y1) * 72 / fig.dpi, label_gap, places=2)
            bottom = xlabel_bbox.y0
        legend_bbox = legend.get_window_extent(renderer)
        self.assertAlmostEqual((bottom - legend_bbox.y1) * 72 / fig.dpi, legend_gap, places=2)
        self.assertAlmostEqual(legend_bbox.x0 + legend_bbox.x1, fig.bbox.width, places=2)

    def assert_dataset_styles(self, fig, expected_colors):
        found_lines = set()
        for ax in fig.axes:
            for line in ax.lines:
                color = line.get_color()
                if color in EXPECTED:
                    self.assertEqual(line.get_marker(), EXPECTED[color])
                    found_lines.add(color)
        self.assertEqual(found_lines, expected_colors)

        found_legend = set()
        for legend in fig.legends:
            for handle in legend.get_lines():
                color = handle.get_color()
                if color in EXPECTED:
                    self.assertEqual(handle.get_marker(), EXPECTED[color])
                    found_legend.add(color)
        self.assertEqual(found_legend, expected_colors)

    def test_plots_and_legends_use_dataset_markers(self):
        data = workstation.load_metrics(INPUT)
        cases = (
            lambda: workstation.create_figure(data, Path("unused"), 300),
            lambda: figure5.main(),
        )
        for index, make_figure in enumerate(cases):
            with self.subTest(figure=make_figure):
                with patch.object(Figure, "savefig"), patch.object(plt, "close"), \
                     patch.object(sys, "argv", ["figure", "--input-csv", str(INPUT)]):
                    make_figure()
                    fig = plt.gcf()
                    self.assert_dataset_styles(fig, set(EXPECTED))
                    if index == 0:
                        self.assert_legend_layout(fig, label_gap=None, legend_gap=22, increase=2)
                        renderer = fig.canvas.get_renderer()
                        distances = [
                            ax.get_window_extent(renderer).x0
                            - ax.yaxis.label.get_window_extent(renderer).x1
                            for ax in fig.axes[::3]
                        ]
                        xlabel = fig._supxlabel.get_window_extent(renderer)
                        x_distance = fig.axes[-1].get_window_extent(renderer).y0 - xlabel.y1
                        self.assertGreater(
                            min(ax.get_tightbbox(renderer).y0 for ax in fig.axes) - xlabel.y1, 0
                        )
                        for distance in distances:
                            self.assertAlmostEqual(distance, x_distance, places=2)
                    else:
                        self.assert_legend_layout(fig)
                    self.assert_chart_font_sizes(fig, increase=2 if index == 0 else 0)
                    if index == 0:
                        self.assertEqual(
                            [ax.get_ylabel() for ax in fig.axes],
                            [
                                "Wall-clock time (sec., log10)", "", "",
                                "Speedup", "", "",
                                "Efficiency (%)", "", "",
                                "Peak RSS (log10)", "", "",
                            ],
                        )
                        self.assertEqual(
                            [ax.get_yscale() for ax in fig.axes[9:]], ["log"] * 3
                        )
                    else:
                        self.assertEqual(fig.axes[0].get_ylabel(), "Wall-clock time (sec., symlog)\n")
                        self.assertTrue(fig.axes[0].texts)
                        self.assertTrue(all(
                            text.get_fontsize() == TYPOGRAPHY["annotation_size"]
                            for text in fig.axes[0].texts
                        ))
                    if index == 0:
                        self.assertTrue(all(
                            any(label.get_visible() for label in ax.get_yticklabels())
                            for ax in fig.axes
                        ))
                        self.assertEqual(
                            fig.legends[0].get_texts()[-1].get_text(),
                            "Ideal scaling/efficiency",
                        )
                plt.close(fig)
        self.assertEqual(figure5.format_duration_label(0.5), "30 sec.")

    def test_supplemental_figure1_legend_layout(self):
        with patch.object(Figure, "savefig"), patch.object(plt, "close"), \
             patch.object(sys, "argv", [
                 "figure", "--input-csv", str(SUPPL1_INPUT), "--output-prefix", "unused",
             ]):
            suppl1.main()
            fig = plt.gcf()
            self.assert_legend_layout(fig)
            self.assert_chart_font_sizes(fig)
            self.assertEqual(fig.axes[1].get_ylabel(), "Max RSS (KB, log10)")
            self.assertEqual(
                [text.get_text() for text in fig.legends[0].get_texts()],
                ["Elapsed time", "Peak memory"],
            )
        plt.close(fig)

    def test_workstation_peak_rss_format_and_values(self):
        data = workstation.load_metrics(INPUT)
        with patch.object(Figure, "savefig"), patch.object(plt, "close"):
            workstation.create_figure(data, Path("unused"), 300)
            fig = plt.gcf()
        self.addCleanup(plt.close, fig)
        for ax, mode in zip(fig.axes[9:], workstation.MODES):
            with self.subTest(mode=mode):
                self.assertEqual(ax.get_yscale(), "log")
                self.assertTrue(ax.get_axisbelow())
                self.assertFalse(any(tick.gridline.get_visible() for tick in ax.yaxis.get_minor_ticks()))
                self.assertEqual(len(ax.lines), len(workstation.DATASETS))
                for line, (dataset, _) in zip(ax.lines, workstation.DATASETS):
                    runs = data[dataset, mode]
                    threads = sorted(runs)
                    self.assertEqual(list(line.get_xdata()), threads)
                    self.assertEqual(list(line.get_ydata()), [runs[t][1] for t in threads])

    def test_workstation_wall_time_format_and_values(self):
        data = workstation.load_metrics(INPUT)
        with patch.object(Figure, "savefig"), patch.object(plt, "close"):
            workstation.create_figure(data, Path("unused"), 300)
            fig = plt.gcf()
        self.addCleanup(plt.close, fig)
        for ax, mode in zip(fig.axes[:3], workstation.MODES):
            with self.subTest(mode=mode):
                self.assertEqual(ax.get_yscale(), "log")
                self.assertEqual(ax.get_axisbelow(), "line")
                self.assertTrue(all(tick.gridline.get_visible() for tick in ax.yaxis.get_minor_ticks()))
                self.assertEqual(len(ax.lines), len(workstation.DATASETS))
                for line, (dataset, _) in zip(ax.lines, workstation.DATASETS):
                    runs = data[dataset, mode]
                    threads = sorted(runs)
                    self.assertEqual(list(line.get_xdata()), threads)
                    self.assertEqual(list(line.get_ydata()), [runs[t][0] for t in threads])

    def test_workstation_equal_panel_gaps(self):
        with patch.object(Figure, "savefig"), patch.object(plt, "close"):
            workstation.create_figure(workstation.load_metrics(INPUT), Path("unused"), 300)
            fig = plt.gcf()
        self.addCleanup(plt.close, fig)
        fig.canvas.draw()
        axes = fig.axes
        boxes = [ax.get_window_extent() for ax in axes]
        column_gaps = [boxes[i + 1].x0 - boxes[i].x1 for i in (0, 1)]
        row_gaps = [boxes[i].y0 - boxes[i + 3].y1 for i in (0, 3, 6)]
        for gap in column_gaps + row_gaps:
            self.assertAlmostEqual(gap, column_gaps[0], places=5)
        self.assertAlmostEqual(boxes[0].y1, fig.subplotpars.top * fig.bbox.height)
        self.assertAlmostEqual(boxes[-1].y0, fig.subplotpars.bottom * fig.bbox.height)
        renderer = fig.canvas.get_renderer()
        for column in range(3):
            labels = axes[column].get_xticklabels()
            label_bottom = min(label.get_window_extent(renderer).y0 for label in labels)
            self.assertGreater(label_bottom, boxes[column + 3].y1)

    def test_workstation_shared_y_axes_per_row(self):
        data = workstation.load_metrics(INPUT)
        cases = (data, {key: runs for key, runs in data.items() if key[1] == "igs"})
        for case in cases:
            with self.subTest(modes={key[1] for key in case}):
                with patch.object(Figure, "savefig"), patch.object(plt, "close"):
                    workstation.create_figure(case, Path("unused"), 300)
                    fig = plt.gcf()
                self.addCleanup(plt.close, fig)
                fig.canvas.draw()
                for start in range(0, 12, 3):
                    row = fig.axes[start:start + 3]
                    reference = row[0]
                    labels = [label.get_text() for label in reference.get_yticklabels()]
                    self.assertTrue(labels)
                    for ax in row:
                        self.assertEqual(ax.get_yscale(), reference.get_yscale())
                        self.assertEqual(ax.get_ylim(), reference.get_ylim())
                        self.assertEqual(list(ax.get_yticks()), list(reference.get_yticks()))
                        self.assertEqual(
                            [label.get_text() for label in ax.get_yticklabels()], labels
                        )
                        lower, upper = ax.get_ylim()
                        for line in ax.lines:
                            for value in line.get_ydata():
                                self.assertLessEqual(lower, value)
                                self.assertLessEqual(value, upper)

    def test_workstation_log2_thread_ticks_in_every_panel(self):
        with patch.object(Figure, "savefig"), patch.object(plt, "close"):
            workstation.create_figure(workstation.load_metrics(INPUT), Path("unused"), 300)
            fig = plt.gcf()
        self.addCleanup(plt.close, fig)
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        threads = [1, 2, 4, 8, 16, 32]
        for index, ax in enumerate(fig.axes):
            with self.subTest(panel=index):
                self.assertEqual(ax.get_xscale(), "log")
                self.assertEqual(ax.xaxis.get_transform().base, 2)
                self.assertEqual(list(ax.get_xticks()), threads)
                labels = ax.get_xticklabels()
                self.assertEqual([label.get_text() for label in labels], [str(t) for t in threads])
                positions = [ax.transData.transform((t, 1))[0] for t in threads]
                gaps = [right - left for left, right in zip(positions, positions[1:])]
                for gap in gaps[1:]:
                    self.assertAlmostEqual(gap, gaps[0])
                bounds = [label.get_window_extent(renderer) for label in labels]
                self.assertTrue(all(
                    not left.overlaps(right)
                    for i, left in enumerate(bounds)
                    for right in bounds[i + 1:]
                ))
                if index < 9:
                    self.assertGreater(min(bound.y0 for bound in bounds), fig.axes[index + 3].get_window_extent().y1)

    def test_workstation_headings_and_vertical_margins(self):
        with patch.object(Figure, "savefig") as savefig, patch.object(plt, "close"):
            workstation.create_figure(workstation.load_metrics(INPUT), Path("unused"), 300)
            fig = plt.gcf()
        self.addCleanup(plt.close, fig)
        self.assertIsNone(fig._suptitle)
        self.assertEqual([ax.get_title() for ax in fig.axes[:3]], list(workstation.MODES))
        self.assertTrue(all(ax.title.get_fontsize() == TYPOGRAPHY["title_size"] + 2 for ax in fig.axes[:3]))
        self.assertTrue(all(not ax.get_title() for ax in fig.axes[3:]))
        fig.canvas.draw()
        content = fig.get_tightbbox(fig.canvas.get_renderer())
        export = savefig.call_args.kwargs["bbox_inches"]
        for margin in (content.y0 - export.y0, export.y1 - content.y1):
            self.assertGreaterEqual(margin, 0)
            self.assertLess(margin, 0.1)

    def test_workstation_portrait_exports(self):
        data = workstation.load_metrics(INPUT)
        with tempfile.TemporaryDirectory() as directory:
            workstation.create_figure(data, Path(directory) / "workstation", 300)
            outputs = list(Path(directory).glob("workstation__*"))
            self.assertEqual({path.suffix for path in outputs}, {".png", ".svg", ".pdf"})
            png = next(path for path in outputs if path.suffix == ".png")
            with Image.open(png) as image:
                self.assertEqual(image.width * 33, image.height * 26)
            svg = next(path for path in outputs if path.suffix == ".svg")
            root = ElementTree.parse(svg).getroot()
            width = float(root.attrib["width"].removesuffix("pt"))
            height = float(root.attrib["height"].removesuffix("pt"))
            self.assertAlmostEqual(width / height, 26 / 33, places=6)

    def test_subset_keeps_marker_assignments(self):
        data = workstation.load_metrics(INPUT)
        selected_datasets = {
            "benchmark_YangEtAl2022_monocots",
            "benchmark_ZhangNNEtAl2025_13724angiosperms",
        }
        selected = {
            key: value for key, value in data.items()
            if key[0] in selected_datasets
        }
        with patch.object(Figure, "savefig"), patch.object(plt, "close"):
            workstation.create_figure(selected, Path("unused"), 300)
            fig = plt.gcf()
            self.assert_dataset_styles(fig, {"#984ea3", "#e41a1c"})
        plt.close(fig)

    def test_dataset_columns_show_mode_metrics(self):
        data = by_dataset.load_metrics(INPUT)
        with patch.object(Figure, "savefig"), patch.object(plt, "close"):
            by_dataset.create_figure(data, Path("unused"), 300)
            fig = plt.gcf()
        self.addCleanup(plt.close, fig)
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        self.assertEqual(len(fig.axes), 20)
        self.assertEqual(
            [ax.get_title().replace("\n", " ") for ax in fig.axes[:5]],
            [label for _, label in by_dataset.DATASETS],
        )
        self.assert_chart_font_sizes(fig, increase=2)
        self.assert_legend_layout(fig, label_gap=None, legend_gap=22, increase=2)
        headings = [ax.title.get_window_extent(renderer) for ax in fig.axes[:5]]
        for left, right in zip(headings, headings[1:]):
            self.assertFalse(left.overlaps(right))
        self.assertEqual(
            [text.get_text() for text in fig.legends[0].get_texts()],
            ["cds", "int", "igs", "Ideal scaling/efficiency"],
        )
        self.assertEqual(
            [ax.lines[0].get_color() for ax in fig.axes[:5]],
            ["#377eb8", "#4daf4a", "#984ea3", "#ff7f00", "#e41a1c"],
        )
        self.assertEqual(
            [line.get_color() for line in fig.legends[0].get_lines()[:3]],
            ["black"] * 3,
        )
        for row in range(4):
            axes = fig.axes[row * 5:(row + 1) * 5]
            for ax, (dataset, _) in zip(axes, by_dataset.DATASETS):
                with self.subTest(row=row, dataset=dataset):
                    self.assertEqual(ax.get_xscale(), "log")
                    self.assertEqual(ax.xaxis.get_transform().base, 2)
                    self.assertEqual(ax.get_ylim(), axes[0].get_ylim())
                    labels = [label.get_window_extent(renderer) for label in ax.get_xticklabels()]
                    for left, right in zip(labels, labels[1:]):
                        self.assertFalse(left.overlaps(right))
                    for mode in by_dataset.MODES:
                        marker, linestyle = by_dataset.MODE_STYLES[mode]
                        lines = [line for line in ax.lines if line.get_marker() == marker]
                        self.assertEqual(len(lines), 1)
                        line = lines[0]
                        self.assertEqual(line.get_color(), workstation.DATASET_COLORS[dataset])
                        runs = data[dataset, mode]
                        threads = sorted(runs)
                        if row == 0:
                            values = [runs[t][0] for t in threads]
                        elif row == 1:
                            values = [runs[1][0] / runs[t][0] for t in threads]
                        elif row == 2:
                            values = [100 * runs[1][0] / runs[t][0] / t for t in threads]
                        else:
                            values = [runs[t][1] for t in threads]
                        self.assertEqual(list(line.get_xdata()), threads)
                        for actual, expected in zip(line.get_ydata(), values):
                            self.assertAlmostEqual(actual, expected)
                        self.assertEqual(line.get_marker(), marker)
                        self.assertEqual(line.get_linestyle(), {"solid": "-", "dashed": "--", "dotted": ":"}[linestyle])

    def test_dataset_columns_without_baseline(self):
        data = by_dataset.load_metrics(INPUT)
        dataset = by_dataset.DATASETS[-1][0]
        runs = data[dataset, "cds"]
        selected = {(dataset, "cds"): {t: value for t, value in runs.items() if t != 1}}
        with patch.object(Figure, "savefig"), patch.object(plt, "close"):
            by_dataset.create_figure(selected, Path("unused"), 300)
            fig = plt.gcf()
        self.addCleanup(plt.close, fig)
        self.assertEqual(len(fig.axes), 4)
        color = workstation.DATASET_COLORS[dataset]
        self.assertEqual(color, "#e41a1c")
        self.assertEqual([sum(line.get_color() == color for line in ax.lines) for ax in fig.axes], [1, 0, 0, 1])

    def test_row_letters(self):
        data = workstation.load_metrics(INPUT)
        for module, columns in ((by_dataset, 5), (workstation, 3)):
            with self.subTest(figure=module.__name__):
                with patch.object(Figure, "savefig") as savefig, patch.object(plt, "close"):
                    module.create_figure(data, Path("unused"), 300)
                    fig = plt.gcf()
                self.addCleanup(plt.close, fig)
                fig.canvas.draw()
                renderer = fig.canvas.get_renderer()
                export = savefig.call_args.kwargs["bbox_inches"]
                for row, letter in enumerate("ABCD"):
                    ax = fig.axes[row * columns]
                    self.assertEqual(len(ax.texts), 1)
                    text = ax.texts[0]
                    self.assertEqual(text.get_text(), letter)
                    self.assertEqual(text.get_fontweight(), "bold")
                    self.assertEqual(text.get_fontsize(), 17)
                    self.assertGreater(text.get_fontsize(), ax.title.get_fontsize())
                    bounds = text.get_window_extent(renderer)
                    self.assertLess(bounds.x1, ax.get_window_extent(renderer).x0)
                    self.assertGreaterEqual(bounds.y0, ax.get_window_extent(renderer).y1)
                    self.assertFalse(bounds.overlaps(ax.title.get_window_extent(renderer)))
                    self.assertGreaterEqual(bounds.x0 / fig.dpi, export.x0)
                    self.assertLessEqual(bounds.y1 / fig.dpi, export.y1)
                    self.assertFalse(bounds.overlaps(ax.yaxis.label.get_window_extent(renderer)))
                    lower, upper = sorted(ax.get_ylim())
                    self.assertTrue(all(
                        not bounds.overlaps(tick.get_window_extent(renderer))
                        for location, tick in zip(ax.get_yticks(), ax.get_yticklabels())
                        if tick.get_visible() and lower <= location <= upper
                    ))
                    if row:
                        previous = fig.axes[(row - 1) * columns]
                        self.assertTrue(all(
                            not bounds.overlaps(tick.get_window_extent(renderer))
                            for tick in previous.get_xticklabels() if tick.get_visible()
                        ))
                self.assertTrue(all(
                    not ax.texts for index, ax in enumerate(fig.axes) if index % columns
                ))


if __name__ == "__main__":
    unittest.main()
