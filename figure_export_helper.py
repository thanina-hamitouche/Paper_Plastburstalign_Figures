"""Prepare Matplotlib figures for publication-sized exports."""

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path

from matplotlib import font_manager, rcParams
from matplotlib.collections import Collection
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, Patch
from matplotlib.text import Text
from matplotlib.transforms import Bbox


with Path(__file__).with_name("figure_typography.json").open(encoding="utf-8") as file:
    TYPOGRAPHY = json.load(file)

DATASET_MARKERS = {
    "benchmark_ZhangNNEtAl2025_53angiosperms": "o",
    "benchmark_YangEtAl2022_Asteraceae": "s",
    "benchmark_YangEtAl2022_monocots": "^",
    "benchmark_YangEtAl2022_angiosperms": "D",
    "benchmark_ZhangNNEtAl2025_13724angiosperms": "v",
}


def configure_typography() -> str:
    available = {
        font.name.casefold(): font.name for font in font_manager.fontManager.ttflist
    }
    families = [TYPOGRAPHY["font_family"], *TYPOGRAPHY["fallback_families"]]
    family = next(
        (available[name.casefold()] for name in families if name.casefold() in available),
        None,
    )
    if family is None:
        raise RuntimeError(f"No supported figure font found: {', '.join(families)}")
    rcParams.update(
        {
            "font.family": family,
            "font.size": TYPOGRAPHY["annotation_size"],
            "axes.labelsize": TYPOGRAPHY["axis_label_size"],
            "xtick.labelsize": TYPOGRAPHY["tick_label_size"],
            "ytick.labelsize": TYPOGRAPHY["tick_label_size"],
            "legend.fontsize": TYPOGRAPHY["legend_size"],
            "axes.titlesize": TYPOGRAPHY["title_size"],
            "mathtext.fontset": "custom",
            "mathtext.cal": family,
            "mathtext.rm": family,
            "mathtext.sf": family,
            "mathtext.it": f"{family}:italic",
            "mathtext.bf": f"{family}:bold",
            "mathtext.bfit": f"{family}:italic:bold",
        }
    )
    return family


def dated_output_paths(prefix: Path) -> dict[str, Path]:
    if not prefix.name:
        raise ValueError("Output prefix must include a filename")
    base = f"{prefix.stem}__{date.today():%Y_%m_%d}"
    return {ext: prefix.parent / f"{base}.{ext}" for ext in ("png", "svg", "pdf")}


def report_output_directory(directory: Path) -> None:
    try:
        location = os.path.relpath(directory)
    except ValueError:
        location = f"{directory.resolve()} (absolute path; relative path unavailable)"
    print(f"Wrote files to {location}")


def add_bottom_legend(fig, handles, ncol=3):
    return fig.legend(
        handles=handles,
        loc="upper center",
        ncol=ncol,
        fontsize=TYPOGRAPHY["legend_size"],
        frameon=False,
        borderaxespad=0,
        borderpad=0,
    )


def place_bottom_legend(fig, legend):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bottom = min(ax.get_tightbbox(renderer).y0 for ax in fig.axes if ax.get_visible())
    if fig._supxlabel is not None and fig._supxlabel.get_visible():
        _, y = fig.transFigure.inverted().transform(
            (0, bottom - renderer.points_to_pixels(8))
        )
        fig._supxlabel.set_position((0.5, y))
        fig._supxlabel.set_verticalalignment("top")
        fig.canvas.draw()
        bottom = fig._supxlabel.get_window_extent(renderer).y0
    gap = renderer.points_to_pixels(16)
    _, y = fig.transFigure.inverted().transform((0, bottom - gap))
    legend.set_bbox_to_anchor((0.5, y), transform=fig.transFigure)


def fit_bbox_to_aspect(content, aspect_ratio, minimum_width=0):
    width = max(minimum_width, content.width, content.height * aspect_ratio)
    height = width / aspect_ratio
    center_x = (content.x0 + content.x1) / 2
    center_y = (content.y0 + content.y1) / 2
    return Bbox.from_bounds(center_x - width / 2, center_y - height / 2, width, height)


def prepare_figure(
    fig, width, bbox_inches=None, pad_inches=0.03, scale_text=False, layout=None,
    bottom_legend=None, aspect_ratio=None,
):
    if bottom_legend is not None:
        place_bottom_legend(fig, bottom_legend)
    fig.canvas.draw()
    if bbox_inches == "tight":
        original_bbox = fig.get_tightbbox(fig.canvas.get_renderer()).padded(pad_inches)
    elif bbox_inches is None:
        original_bbox = fig.bbox_inches
    else:
        original_bbox = bbox_inches

    scale = width / original_bbox.width
    fig.set_size_inches(fig.get_size_inches() * scale)
    if scale_text:
        for text in fig.findobj(match=Text):
            text.set_fontsize(text.get_fontsize() * scale)
    for line in fig.findobj(match=Line2D):
        line.set_linewidth(line.get_linewidth() * scale)
        line.set_markersize(line.get_markersize() * scale)
    for patch in fig.findobj(match=Patch):
        patch.set_linewidth(patch.get_linewidth() * scale)
        if isinstance(patch, FancyArrowPatch):
            patch.set_mutation_scale(patch.get_mutation_scale() * scale)
    for collection in fig.findobj(match=Collection):
        collection.set_linewidths(collection.get_linewidths() * scale)
        if hasattr(collection, "get_sizes"):
            collection.set_sizes(collection.get_sizes() * scale**2)

    if layout is not None:
        fig.tight_layout(**layout)

    if bottom_legend is not None:
        place_bottom_legend(fig, bottom_legend)

    if bbox_inches is None:
        return None

    fig.canvas.draw()
    content = fig.get_tightbbox(fig.canvas.get_renderer()).padded(pad_inches * scale)
    aspect = (
        aspect_ratio if aspect_ratio is not None else original_bbox.width / original_bbox.height
    )
    return fit_bbox_to_aspect(content, aspect, minimum_width=width)
