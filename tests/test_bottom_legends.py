import unittest

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.lines import Line2D

from CODE_SupplFig2_Effectiveness_Multithreading import (
    DATASET_LABELS,
    DATASET_ORDER,
    MARKER_ORDER,
    add_horizontal_bottom_legend,
)
from figure_export_helper import configure_typography, prepare_figure


class BottomLegendTests(unittest.TestCase):
    def test_gap_after_export_resize_and_layout(self):
        configure_typography()
        fig, axes = plt.subplots(1, 2, figsize=(8, 4))
        canvas = FigureCanvasAgg(fig)
        self.addCleanup(plt.close, fig)
        axes[0].set_xlabel("First axis")
        axes[1].set_xlabel("Second axis\nwith a longer label")
        legend = fig.legend(
            handles=[Line2D([], [], label="Series")],
            loc="upper center",
            borderaxespad=0,
            borderpad=0,
        )
        rect = (0, 0.1, 1, 1)
        fig.tight_layout(rect=rect)
        prepare_figure(
            fig, 12, bbox_inches="tight", layout={"rect": rect}, bottom_legend=legend
        )
        canvas.draw()
        renderer = canvas.get_renderer()
        bottom = min(ax.get_tightbbox(renderer).y0 for ax in axes)
        gap = (bottom - legend.get_window_extent(renderer).y1) * 72 / fig.dpi
        self.assertAlmostEqual(gap, 16, places=2)

    def test_requested_aspect_contains_all_content(self):
        configure_typography()
        for size in ((8, 3), (3, 8)):
            with self.subTest(size=size):
                fig, ax = plt.subplots(figsize=size)
                canvas = FigureCanvasAgg(fig)
                self.addCleanup(plt.close, fig)
                ax.set_xlabel("Threads")
                legend = fig.legend(
                    handles=[Line2D([], [], label="Series")],
                    loc="upper center", borderaxespad=0, borderpad=0,
                )
                bbox = prepare_figure(
                    fig, 12, bbox_inches="tight", bottom_legend=legend, aspect_ratio=2
                )
                assert bbox is not None
                canvas.draw()
                content = fig.get_tightbbox(canvas.get_renderer())
                self.assertAlmostEqual(bbox.width / bbox.height, 2)
                self.assertLessEqual(bbox.x0, content.x0)
                self.assertLessEqual(bbox.y0, content.y0)
                self.assertGreaterEqual(bbox.x1, content.x1)
                self.assertGreaterEqual(bbox.y1, content.y1)

    def test_supplemental_legend_is_one_grouped_block(self):
        configure_typography()
        for datasets in (DATASET_ORDER, DATASET_ORDER[:1]):
            with self.subTest(datasets=datasets):
                fig, _ = plt.subplots()
                canvas = FigureCanvasAgg(fig)
                self.addCleanup(plt.close, fig)
                legend = add_horizontal_bottom_legend(fig, datasets)
                canvas.draw()
                self.assertEqual(len(fig.legends), 1)
                texts = {text.get_text(): text for text in legend.get_texts() if text.get_text()}
                expected = {"DATASET", "MARKER", *MARKER_ORDER}
                expected.update(DATASET_LABELS[dataset] for dataset in datasets)
                self.assertEqual(set(texts), expected)
                renderer = canvas.get_renderer()
                dataset_bottom = min(
                    texts[DATASET_LABELS[dataset]].get_window_extent(renderer).y0
                    for dataset in datasets
                )
                marker_top = texts["MARKER"].get_window_extent(renderer).y1
                self.assertGreater(dataset_bottom, marker_top)


if __name__ == "__main__":
    unittest.main()
