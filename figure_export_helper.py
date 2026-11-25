"""Prepare Matplotlib figures for publication-sized exports."""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

from matplotlib.collections import Collection
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, Patch
from matplotlib.text import Text
from matplotlib.transforms import Bbox


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


def prepare_figure(fig, width, bbox_inches=None, pad_inches=0.1):
    fig.canvas.draw()
    if bbox_inches == "tight":
        original_bbox = fig.get_tightbbox(fig.canvas.get_renderer()).padded(pad_inches)
    elif bbox_inches is None:
        original_bbox = fig.bbox_inches
    else:
        original_bbox = bbox_inches

    scale = width / original_bbox.width
    fig.set_size_inches(fig.get_size_inches() * scale)
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

    if bbox_inches is None:
        return None

    fig.canvas.draw()
    content = fig.get_tightbbox(fig.canvas.get_renderer()).padded(pad_inches * scale)
    aspect = original_bbox.width / original_bbox.height
    final_width = max(width, content.width, content.height * aspect)
    final_height = final_width / aspect
    center_x = (content.x0 + content.x1) / 2
    center_y = (content.y0 + content.y1) / 2
    return Bbox.from_bounds(
        center_x - final_width / 2,
        center_y - final_height / 2,
        final_width,
        final_height,
    )
