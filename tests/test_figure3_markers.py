import runpy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
from matplotlib.figure import Figure
from matplotlib.patches import Polygon, Rectangle


SCRIPT = Path(__file__).resolve().parents[1] / "CODE_Figure3_OverviewWorkflow.py"


class Figure3MarkerTests(unittest.TestCase):
    def test_extraction_marker_patterns(self):
        with patch.object(sys, "argv", [str(SCRIPT)]), \
             patch.object(Figure, "savefig"), patch.object(plt, "close"):
            result = runpy.run_path(str(SCRIPT))
        fig, ax = result["fig"], result["ax"]
        self.addCleanup(plt.close, fig)

        black, white = to_rgba("black"), to_rgba("white")
        for y, exon_colors, intron_color in [
            (7.14, [black, black, white], white),
            (6.76, [white, white, white], black),
            (6.38, [white, white, white], white),
            (6.00, [white, white, black], white),
        ]:
            with self.subTest(y=y):
                exons = [
                    p for p in ax.patches
                    if isinstance(p, Polygon)
                    and abs(p.get_xy()[0, 1] - (y - 0.09)) < 1e-6
                    and 5.17 <= p.get_xy()[0, 0] <= 6.37
                ]
                self.assertEqual([p.get_facecolor() for p in exons], exon_colors)
                introns = [
                    p for p in ax.patches
                    if isinstance(p, Rectangle)
                    and abs(p.get_x() - 5.44) < 1e-6
                    and abs(p.get_y() - (y - 0.045)) < 1e-6
                ]
                self.assertEqual([p.get_facecolor() for p in introns], [intron_color])

        stripes = [
            p for p in ax.patches
            if isinstance(p, Rectangle)
            and 5.90 - 1e-6 <= p.get_x() < 6.17
            and abs(p.get_y() - (6.38 - 0.09)) < 1e-6
            and p.get_fill()
        ]
        self.assertEqual([p.get_facecolor() for p in stripes], [black, white, black, white])


if __name__ == "__main__":
    unittest.main()
