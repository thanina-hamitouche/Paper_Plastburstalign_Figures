import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

import CODE_Figure4_Speedup_and_Wallclocktime as figure4
import CODE_Figure5_Differences_across_datasets as figure5
import CODE_SupplFig1_ParallelismTypes_Asteraceae_CDS as suppl1
import CODE_SupplFig2_Effectiveness_Multithreading as suppl2
import CODE_SupplFig3_peakMem_speedup as suppl3
from figure_export_helper import TYPOGRAPHY


INPUT = Path(__file__).resolve().parents[1] / "input_data" / "DATA_Benchmarking_on_Workstation__2026_11_24.csv"
SUPPL1_INPUT = Path(__file__).resolve().parents[1] / "input_data" / "DATA_ParallelismTypes_Asteraceae_CDS__2026_11_23.csv"
EXPECTED = {
    "#377eb8": "o",
    "#4daf4a": "s",
    "#984ea3": "^",
    "#ff7f00": "D",
    "#e41a1c": "v",
}


class DatasetMarkerTests(unittest.TestCase):
    def assert_legend_layout(self, fig):
        self.assertEqual(len(fig.legends), 1)
        legend = fig.legends[0]
        self.assertTrue(all(
            text.get_fontsize() == TYPOGRAPHY["legend_size"]
            for text in legend.get_texts()
        ))
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        bottom = min(ax.get_tightbbox(renderer).y0 for ax in fig.axes if ax.get_visible())
        if fig._supxlabel is not None and fig._supxlabel.get_visible():
            xlabel_bbox = fig._supxlabel.get_window_extent(renderer)
            self.assertAlmostEqual((bottom - xlabel_bbox.y1) * 72 / fig.dpi, 8, places=2)
            bottom = xlabel_bbox.y0
        legend_bbox = legend.get_window_extent(renderer)
        self.assertAlmostEqual((bottom - legend_bbox.y1) * 72 / fig.dpi, 16, places=2)
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
        data = figure5.load_metrics(INPUT)
        cases = (
            lambda: figure4.make_plots(INPUT, Path(".")),
            lambda: figure5.create_figure(data, Path("unused"), 300, INPUT),
            lambda: suppl3.draw(INPUT, Path("unused")),
            lambda: suppl2.main(),
        )
        benchmark_legends = []
        supplemental_axis_sizes = {}
        for index, make_figure in enumerate(cases):
            with self.subTest(figure=make_figure):
                with patch.object(Figure, "savefig") as savefig, patch.object(plt, "close"), \
                     patch.object(suppl2, "adjust_text", None), \
                     patch.object(sys, "argv", ["figure", "--input-csv", str(INPUT)]):
                    make_figure()
                    fig = plt.gcf()
                    self.assert_dataset_styles(fig, set(EXPECTED))
                    self.assert_legend_layout(fig)
                    if index == 0:
                        self.assertEqual(
                            [ax.get_title() for ax in fig.axes],
                            ["cds", "int", "igs", "", "", ""],
                        )
                        self.assertEqual(fig.axes[0].get_ylabel(), "Speedup")
                        self.assertEqual(
                            fig.axes[3].get_ylabel(), "Wall-clock time (sec., log scale)"
                        )
                    elif index == 1:
                        self.assertEqual(
                            [ax.get_ylabel() for ax in fig.axes],
                            [
                                "Elapsed (sec.)", "", "",
                                "Speedup", "", "",
                                "Efficiency (%)", "", "",
                                "Peak RSS (log10)", "", "",
                            ],
                        )
                        self.assertEqual(
                            [ax.get_yscale() for ax in fig.axes[9:]], ["log"] * 3
                        )
                    elif index == 2:
                        self.assertEqual(
                            [ax.get_ylabel() for ax in fig.axes],
                            ["Peak RSS (log10)", "", "", "Speedup", "", ""],
                        )
                        self.assertEqual(
                            [ax.get_yscale() for ax in fig.axes[:3]], ["log"] * 3
                        )
                        renderer = fig.canvas.get_renderer()
                        for ax in fig.axes[3:]:
                            labels = [label for label in ax.get_xticklabels() if label.get_visible()]
                            bounds = [label.get_window_extent(renderer) for label in labels]
                            self.assertTrue(all(
                                not left.overlaps(right)
                                for i, left in enumerate(bounds)
                                for right in bounds[i + 1:]
                            ))
                    else:
                        self.assertEqual(fig.axes[0].get_ylabel(), "Wall-clock time (symlog)\n")
                    if index in (1, 2):
                        self.assertTrue(all(
                            any(label.get_visible() for label in ax.get_yticklabels())
                            for ax in fig.axes
                        ))
                    if index in (2, 3):
                        width = savefig.call_args.kwargs["bbox_inches"].width
                        supplemental_axis_sizes[index] = (
                            fig.axes[0].yaxis.label.get_fontsize() / width,
                            fig.axes[0].get_yticklabels()[0].get_fontsize() / width,
                        )
                    if index < 3:
                        legend = fig.legends[0]
                        benchmark_legends.append([
                            (text.get_text(), line.get_color(), line.get_marker(), line.get_linestyle())
                            for text, line in zip(legend.get_texts(), legend.get_lines())
                        ])
                plt.close(fig)
        self.assertEqual(benchmark_legends[0], benchmark_legends[1])
        self.assertEqual(benchmark_legends[1], benchmark_legends[2])
        for size3, size2 in zip(supplemental_axis_sizes[2], supplemental_axis_sizes[3]):
            self.assertAlmostEqual(size3 / size2, 1, delta=0.05)
        self.assertEqual(suppl2.format_duration_label(0.5), "30 sec.")

    def test_supplemental_figure1_legend_layout(self):
        with patch.object(Figure, "savefig"), patch.object(plt, "close"), \
             patch.object(sys, "argv", [
                 "figure", "--input-csv", str(SUPPL1_INPUT), "--output-prefix", "unused",
             ]):
            suppl1.main()
            fig = plt.gcf()
            self.assert_legend_layout(fig)
            self.assertEqual(fig.axes[1].get_ylabel(), "Max RSS (KB, log10)")
            self.assertEqual(
                [text.get_text() for text in fig.legends[0].get_texts()],
                ["Elapsed time", "Peak memory"],
            )
        plt.close(fig)

    def test_subset_keeps_marker_assignments(self):
        data = figure5.load_metrics(INPUT)
        selected_datasets = {
            "benchmark_YangEtAl2022_monocots",
            "benchmark_ZhangNNEtAl2025_13724angiosperms",
        }
        selected = {
            key: value for key, value in data.items()
            if key[0] in selected_datasets
        }
        for make_figure in (
            lambda: figure5.create_figure(selected, Path("unused"), 300, INPUT),
            lambda: suppl3.draw(INPUT, Path("unused")),
        ):
            with self.subTest(figure=make_figure):
                with patch.object(Figure, "savefig"), patch.object(plt, "close"), \
                     patch.object(suppl3, "load_rows", return_value=selected):
                    make_figure()
                    fig = plt.gcf()
                    self.assert_dataset_styles(fig, {"#984ea3", "#e41a1c"})
                plt.close(fig)


if __name__ == "__main__":
    unittest.main()
