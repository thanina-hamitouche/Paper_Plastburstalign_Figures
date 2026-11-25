import argparse
import os
from datetime import date

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgba
from matplotlib.patches import Arc, Polygon, Rectangle, Wedge

LABEL_FONTSIZE = 14
PANEL_LABEL_FONTSIZE = 20
SPLIT_ALIGNMENT_GAP_STRETCH = 2.0
LEFT_PANEL_LEFT = -7.0
LEFT_PANEL_RIGHT = 7.0
GENE_ARC_LINEWIDTH = 14
ARC_OUTLINE_EXTRA_WIDTH = 1
BAR_OUTLINE_LINEWIDTH = 0.5
GENE_ARROWHEAD_LENGTH = 0.55
IR_SPANS = {
    "T1": (219.2, 255.8, 284.2, 329.8),
    "T2": (210, 257, 283, 324),
    "T3": (219, 251, 289, 321),
}


# ---------------------------
# Helper functions
# ---------------------------
def polar_to_cart(r, theta_deg):
    theta = np.deg2rad(theta_deg)
    return r * np.cos(theta), r * np.sin(theta)


def circular_gene_vertices(center, radius, start, end, height, clockwise=False):
    span = (end - start) % 360
    head_angle = min(np.rad2deg(GENE_ARROWHEAD_LENGTH / radius), span / 2)
    shaft_start = start + head_angle if clockwise else start
    shaft_end = start + span if clockwise else start + span - head_angle
    angles = np.deg2rad(
        np.linspace(shaft_start, shaft_end, max(2, int(np.ceil(span)) + 1))
    )
    outer = np.column_stack(
        (
            center[0] + (radius + height / 2) * np.cos(angles),
            center[1] + (radius + height / 2) * np.sin(angles),
        )
    )
    inner = np.column_stack(
        (
            center[0] + (radius - height / 2) * np.cos(angles[::-1]),
            center[1] + (radius - height / 2) * np.sin(angles[::-1]),
        )
    )
    tip_x, tip_y = polar_to_cart(radius, start if clockwise else start + span)
    tip = (center[0] + tip_x, center[1] + tip_y)
    return (
        np.vstack((outer, inner, tip)) if clockwise else np.vstack((outer, tip, inner))
    )


def linear_gene_vertices(x, y, width, height):
    head_length = min(GENE_ARROWHEAD_LENGTH, width / 2)
    return [
        (x, y - height / 2),
        (x + width - head_length, y - height / 2),
        (x + width, y),
        (x + width - head_length, y + height / 2),
        (x, y + height / 2),
    ]


def draw_gene_arrow(ax, x, y, width, height, color):
    arrow = Polygon(
        linear_gene_vertices(x, y, width, height),
        closed=True,
        facecolor=color,
        edgecolor="black",
        linewidth=BAR_OUTLINE_LINEWIDTH,
        zorder=2,
    )
    ax.add_patch(arrow)
    return arrow


def draw_arc(
    ax,
    center,
    r,
    start,
    end,
    color,
    lw=4,
    alpha=0.95,
    hatch=None,
    fill=False,
    edgecolor=None,
    add_outline=False,
):
    cx, cy = center

    # Add thin black outline underneath if requested (draw first so it's behind)
    if add_outline:
        outline_arc = Arc(
            (cx, cy),
            width=2 * r,
            height=2 * r,
            theta1=start,
            theta2=end,
            color="black",
            lw=lw + ARC_OUTLINE_EXTRA_WIDTH,
            alpha=1.0,
        )
        ax.add_patch(outline_arc)

        # Add radial lines at start and end of arc (the "sides")
        # Arc thickness in data units (rough approximation based on linewidth)
        thickness_offset = (
            lw * 0.026
        )  # Adjust this factor to match visual arc thickness
        inner_r = r - thickness_offset
        outer_r = r + thickness_offset

        # Start edge
        x1_start, y1_start = polar_to_cart(inner_r, start)
        x2_start, y2_start = polar_to_cart(outer_r, start)
        ax.plot(
            [cx + x1_start, cx + x2_start],
            [cy + y1_start, cy + y2_start],
            color="black",
            lw=0.5,
            solid_capstyle="butt",
        )

        # End edge
        x1_end, y1_end = polar_to_cart(inner_r, end)
        x2_end, y2_end = polar_to_cart(outer_r, end)
        ax.plot(
            [cx + x1_end, cx + x2_end],
            [cy + y1_end, cy + y2_end],
            color="black",
            lw=0.5,
            solid_capstyle="butt",
        )

    if fill:
        # For filled arc with hatching
        arc = Arc(
            (cx, cy),
            width=2 * r,
            height=2 * r,
            theta1=start,
            theta2=end,
            color=edgecolor if edgecolor else color,
            lw=lw,
            alpha=alpha,
            fill=False,
            hatch=hatch,
        )
    else:
        arc = Arc(
            (cx, cy),
            width=2 * r,
            height=2 * r,
            theta1=start,
            theta2=end,
            color=color,
            lw=lw,
            alpha=alpha,
        )
    ax.add_patch(arc)


def draw_hatched_arc(ax, center, r, start, end, color1, color2, width):
    """Draw a thick arc with slanted ribbon pattern showing two colors."""
    cx, cy = center

    # Fixed segment width in degrees for consistent ribbon pattern
    segment_size = 3.0  # degrees

    # Calculate arc span
    arc_span = end - start if end >= start else 360 - start + end
    num_segments = int(arc_span / segment_size)

    # Create alternating slanted ribbon segments with fixed width
    for i in range(num_segments):
        segment_start = start + i * segment_size
        segment_end = start + (i + 1) * segment_size
        color = color1 if i % 2 == 0 else color2

        wedge = Wedge(
            center,
            r + width / 2,
            segment_start,
            segment_end,
            width=width,
            facecolor=color,
            edgecolor=color,
            alpha=0.9,
            linewidth=0,
        )
        ax.add_patch(wedge)

    # Handle remaining partial segment if any
    remaining = arc_span - (num_segments * segment_size)
    if remaining > 0.5:  # Only draw if significant
        segment_start = start + num_segments * segment_size
        segment_end = end
        color = color1 if num_segments % 2 == 0 else color2
        wedge = Wedge(
            center,
            r + width / 2,
            segment_start,
            segment_end,
            width=width,
            facecolor=color,
            edgecolor=color,
            alpha=0.9,
            linewidth=0,
        )
        ax.add_patch(wedge)

    # Add black outline around entire striped arc
    outline_outer = Arc(
        (cx, cy),
        width=2 * (r + width / 2),
        height=2 * (r + width / 2),
        theta1=start,
        theta2=end,
        color="black",
        lw=0.5,
        alpha=1.0,
    )
    ax.add_patch(outline_outer)
    outline_inner = Arc(
        (cx, cy),
        width=2 * (r - width / 2),
        height=2 * (r - width / 2),
        theta1=start,
        theta2=end,
        color="black",
        lw=0.5,
        alpha=1.0,
    )
    ax.add_patch(outline_inner)

    # Add radial end caps at start and end of arc
    inner_r = r - width / 2
    outer_r = r + width / 2

    # Start edge
    x1_start, y1_start = polar_to_cart(inner_r, start)
    x2_start, y2_start = polar_to_cart(outer_r, start)
    ax.plot(
        [cx + x1_start, cx + x2_start],
        [cy + y1_start, cy + y2_start],
        color="black",
        lw=0.5,
        solid_capstyle="butt",
    )

    # End edge
    x1_end, y1_end = polar_to_cart(inner_r, end)
    x2_end, y2_end = polar_to_cart(outer_r, end)
    ax.plot(
        [cx + x1_end, cx + x2_end],
        [cy + y1_end, cy + y2_end],
        color="black",
        lw=0.5,
        solid_capstyle="butt",
    )


def dotted_line(ax, x1, y1, x2, y2, dotsize=4, lw=1.0, zorder=0):
    xs = np.linspace(x1, x2, 40)
    ys = np.linspace(y1, y2, 40)
    ax.plot(xs, ys, linestyle=":", color="black", linewidth=lw, zorder=zorder)


def draw_box(ax, x, y_center, w, h, color, is_intron=False):
    rect_h = h / 2.0 if is_intron else h
    rect = Rectangle(
        (x, y_center - rect_h / 2),
        w,
        rect_h,
        fill=True,
        facecolor=color,
        edgecolor="black",
        linewidth=BAR_OUTLINE_LINEWIDTH,
        zorder=2,
    )
    ax.add_patch(rect)


def draw_striped_box(ax, x, y_center, w, h, color1, color2):
    """Draw a box with alternating vertical stripes of two colors."""
    segment_width = min(0.15, w / 2)
    num_segments = int(w / segment_width)

    for i in range(num_segments):
        stripe_x = x + i * segment_width
        stripe_w = min(segment_width, w - i * segment_width)
        color = color1 if i % 2 == 0 else color2

        rect = Rectangle(
            (stripe_x, y_center - h / 2),
            stripe_w,
            h,
            fill=True,
            facecolor=color,
            lw=0,
            zorder=2,
            alpha=0.9,
        )
        ax.add_patch(rect)

    # Handle remaining partial stripe
    remaining = w - (num_segments * segment_width)
    if remaining > 0.01:
        stripe_x = x + num_segments * segment_width
        color = color1 if num_segments % 2 == 0 else color2
        rect = Rectangle(
            (stripe_x, y_center - h / 2),
            remaining,
            h,
            fill=True,
            facecolor=color,
            lw=0,
            zorder=2,
            alpha=0.9,
        )
        ax.add_patch(rect)

    # Add black outline around entire striped box
    outline = Rectangle(
        (x, y_center - h / 2),
        w,
        h,
        fill=False,
        edgecolor="black",
        linewidth=0.5,
        zorder=3,
    )
    ax.add_patch(outline)


def add_origin_marker(ax, center, R, angle_deg=0.0):
    """Mark the replication origin at a given angle with a short tick and upward triangle."""
    inner_r = R - 0.2
    outer_r = R + 0.4
    tri_r = R + 0.6
    cx, cy = center
    x0, y0 = polar_to_cart(inner_r, angle_deg)
    x1, y1 = polar_to_cart(outer_r, angle_deg)
    xt, yt = polar_to_cart(tri_r, angle_deg)
    ax.plot([cx + x0, cx + x1], [cy + y0, cy + y1], color="black", lw=1.5, zorder=3)
    ax.scatter(cx + xt, cy + yt, marker="^", color="black", s=35, zorder=4)


def shift_gene_data(gene_data, offset_deg):
    """Return a copy of gene_data with start/end shifted by offset_deg (counter-clockwise)."""
    shifted = {}
    for genome, items in gene_data.items():
        shifted_items = []
        for elem in items:
            new_elem = dict(elem)
            if "start" in new_elem and "end" in new_elem:
                new_elem["start"] = (new_elem["start"] - offset_deg) % 360
                new_elem["end"] = (new_elem["end"] - offset_deg) % 360
            shifted_items.append(new_elem)
        shifted[genome] = shifted_items
    return shifted


def to_plot_angle(angle_deg):
    """Map data angles (0° at right, increasing counter-clockwise) to Matplotlib angles (0° at +x, CCW)."""
    return angle_deg % 360


def get_width(element, InnerR):
    """Calculate width from start and end degree positions, handling wrapped angles."""
    if element["end"] >= element["start"]:
        angle_span = element["end"] - element["start"]
    else:
        angle_span = 360 - element["start"] + element["end"]
    return (angle_span / 180.0) * np.pi * InnerR


def get_genes_only(genome_key, gene_data):
    """Extract only genes and introns (not IGS) from genome data."""
    return [elem for elem in gene_data[genome_key] if elem.get("type") not in ["IGS"]]


def get_genes_no_introns(genome_key, gene_data):
    """Extract only genes (not IGS or introns) from genome data."""
    return [elem for elem in gene_data[genome_key] if elem.get("type") == "gene"]


def group_gene_segments(genome_key, gene_data):
    """Group consecutive gene/intron elements of same color into composite gene structures.
    Returns list where each item is either a single element or a list of segments (exon-intron-exon)."""
    elements = get_genes_only(genome_key, gene_data)
    if not elements:
        return []

    grouped = []
    idx = 0
    while idx < len(elements):
        current_element = elements[idx]
        # Check if next elements are same color gene/intron
        segment_group = [current_element]
        next_idx = idx + 1
        while next_idx < len(elements) and elements[next_idx].get(
            "color"
        ) == current_element.get("color"):
            segment_group.append(elements[next_idx])
            next_idx += 1

        # If group has multiple elements (exon-intron-exon), keep as list; else unwrap
        if len(segment_group) > 1:
            grouped.append(segment_group)
            idx = next_idx
        else:
            grouped.append(current_element)
            idx += 1

    return grouped


def find_flanking_gene_colors(elements, igs_index):
    """Find the colors of genes flanking an IGS element.
    Returns tuple of (previous_gene_color, next_gene_color)."""
    prev_gene_color = None
    next_gene_color = None
    num_elements = len(elements)

    # Look backward for previous gene
    for j in range(igs_index - 1, -1, -1):
        if elements[j].get("type") == "gene":
            prev_gene_color = elements[j]["color"]
            break
    # Wrap around to end if not found
    if prev_gene_color is None:
        for j in range(num_elements - 1, igs_index, -1):
            if elements[j].get("type") == "gene":
                prev_gene_color = elements[j]["color"]
                break

    # Look forward for next gene
    for j in range(igs_index + 1, num_elements):
        if elements[j].get("type") == "gene":
            next_gene_color = elements[j]["color"]
            break
    # Wrap around to start if not found
    if next_gene_color is None:
        for j in range(igs_index):
            if elements[j].get("type") == "gene":
                next_gene_color = elements[j]["color"]
                break

    return prev_gene_color, next_gene_color


def normalize_wedge_spans(wedge1_start, wedge1_end, wedge2_start, wedge2_end):
    """Ensure both wedges have the same angular span by adjusting to the larger span.
    Returns normalized (wedge1_start, wedge1_end, wedge2_start, wedge2_end)."""
    span1 = wedge1_end - wedge1_start
    span2 = wedge2_end - wedge2_start

    if abs(span1 - span2) < 0.01:  # Already equal (within tolerance)
        return wedge1_start, wedge1_end, wedge2_start, wedge2_end

    # Use the larger span
    target_span = max(span1, span2)

    # Adjust wedge 1 if needed
    if span1 < target_span:
        diff = target_span - span1
        wedge1_start -= diff / 2
        wedge1_end += diff / 2

    # Adjust wedge 2 if needed
    if span2 < target_span:
        diff = target_span - span2
        wedge2_start -= diff / 2
        wedge2_end += diff / 2

    return wedge1_start, wedge1_end, wedge2_start, wedge2_end


# ---------------------------
# Left-side panel (circles and arcs)
# ---------------------------


def draw_left_panel(ax, gene_data, R, InnerR, igs_width):
    """Draw circles with arcs using gene position data (start and end angles)."""
    y_top, spacing = 18.0, -11.0
    centers = [(0, y_top), (0, y_top + spacing), (0, y_top + 2 * spacing)]
    labels = ["T1", "T2", "T3"]
    genomes = ["T1", "T2", "T3"]
    gene_arrows = []

    panel_left = LEFT_PANEL_LEFT
    panel_right = LEFT_PANEL_RIGHT
    panel_bottom = centers[-1][1] - R - 1.0
    panel_top = centers[0][1] + R + 1.0
    ax.add_patch(
        Rectangle(
            (panel_left, panel_bottom),
            panel_right - panel_left,
            panel_top - panel_bottom,
            facecolor="#f2f2f2",
            edgecolor="none",
            zorder=-10,
        )
    )
    ax.text(
        panel_left + 0.7,
        panel_top - 0.7,
        "A",
        ha="left",
        va="top",
        fontsize=PANEL_LABEL_FONTSIZE,
        fontweight="bold",
        zorder=20,
    )

    IGS_R = InnerR - 1.2  # Inner circle for IGS markers (smaller diameter)

    for center, label, genome_key in zip(centers, labels, genomes):
        # Draw inverted-repeat background wedges behind genes
        # Normalize wedge spans to ensure both wedges have equal angular extent
        wedge1_start, wedge1_end, wedge2_start, wedge2_end = normalize_wedge_spans(
            *IR_SPANS[genome_key]
        )

        ir_wedge1 = Wedge(
            center,
            InnerR,
            to_plot_angle(wedge1_start),
            to_plot_angle(wedge1_end),
            facecolor="#d96c6c",
            edgecolor="none",
            alpha=0.3,
            zorder=0,
        )
        ax.add_patch(ir_wedge1)
        ir_wedge2 = Wedge(
            center,
            InnerR,
            to_plot_angle(wedge2_start),
            to_plot_angle(wedge2_end),
            facecolor="#d96c6c",
            edgecolor="none",
            alpha=0.3,
            zorder=0,
        )
        ax.add_patch(ir_wedge2)

        # Draw fine black circle at gene/intron radius
        ax.add_patch(plt.Circle(center, InnerR, fill=False, color="black", lw=1))
        # Origin marker at outer radius
        add_origin_marker(ax, center, R, angle_deg=to_plot_angle(0.0))

        # Draw IGS markers on inner circle with ribbon pattern from flanking genes
        genome_elements = gene_data[genome_key]
        for element_idx, element in enumerate(genome_elements):
            if element.get("type") == "IGS":
                start_angle = to_plot_angle(element["start"])
                end_angle = to_plot_angle(element["end"])

                # Find flanking gene colors
                prev_gene_color, next_gene_color = find_flanking_gene_colors(
                    genome_elements, element_idx
                )

                # Draw with ribbon pattern using both colors
                if prev_gene_color and next_gene_color:
                    draw_hatched_arc(
                        ax,
                        center,
                        IGS_R,
                        start_angle,
                        end_angle,
                        prev_gene_color,
                        next_gene_color,
                        width=igs_width,
                    )
                else:
                    draw_arc(
                        ax, center, IGS_R, start_angle, end_angle, color="gray", lw=8
                    )

        # Draw genes and introns
        for element in gene_data[genome_key]:
            start_angle = to_plot_angle(element["start"])
            end_angle = to_plot_angle(element["end"])
            if element.get("type") == "intron":
                # Introns: much thinner than genes
                draw_arc(
                    ax,
                    center,
                    InnerR,
                    start_angle,
                    end_angle,
                    color=element["color"],
                    lw=3,
                    add_outline=True,
                )
            elif element.get("type") == "gene":
                clockwise = element.get("clockwise", False)
                arrow = Polygon(
                    circular_gene_vertices(
                        center, InnerR, start_angle, end_angle, igs_width, clockwise
                    ),
                    closed=True,
                    facecolor=to_rgba(element["color"], 0.95),
                    edgecolor="black",
                    linewidth=BAR_OUTLINE_LINEWIDTH,
                    zorder=2,
                )
                ax.add_patch(arrow)
                gene_arrows.append(
                    (arrow, center, InnerR, start_angle, end_angle, clockwise)
                )
        ax.text(
            center[0],
            center[1],
            label,
            ha="center",
            va="center",
            fontsize=LABEL_FONTSIZE,
        )

    return centers, gene_arrows


# ---------------------------
# Right-side panels
# ---------------------------


def alignment_genewise(
    ax, InnerR, gene_data, panel_x0, box_h, base_y, row_spacing, header_offset=0.9
):
    """Draw gene-wise columns, excluding introns and duplicated IR portions."""
    linear_gap = SPLIT_ALIGNMENT_GAP_STRETCH * (10.0 / 180.0) * np.pi * InnerR

    genes_by_genome = {}
    for genome in ["T1", "T2", "T3"]:
        groups = []
        for gene in get_genes_no_introns(genome, gene_data):
            if groups and groups[-1][-1].get("merge_next_cds", False):
                groups[-1].append(gene)
            else:
                groups.append([gene])
        genes_by_genome[genome] = groups[:-1]
    gene_count = len(genes_by_genome["T1"])

    # Column widths: max width for each gene across genomes
    col_widths = []
    for i in range(gene_count):
        widths = [
            sum(get_width(segment, InnerR) for segment in genes_by_genome[g][i])
            for g in ["T1", "T2", "T3"]
        ]
        col_widths.append(max(widths))

    # Column start positions
    col_starts = [0.8]
    for i in range(gene_count - 1):
        col_starts.append(col_starts[-1] + col_widths[i] + linear_gap)

    header_y = base_y + header_offset

    y_positions = [base_y + i * row_spacing for i in range(3)]

    def build_row(genome_key):
        genes = genes_by_genome[genome_key]
        result = []
        for i in range(gene_count):
            segments = genes[i]
            result.append(
                {
                    "x": panel_x0 + col_starts[i],
                    "w": sum(get_width(segment, InnerR) for segment in segments),
                    "color": segments[0]["color"],
                }
            )
        return result

    rows = [
        (build_row("T1"), y_positions[0]),
        (build_row("T2"), y_positions[1]),
        (build_row("T3"), y_positions[2]),
    ]

    _, _, _, t3_ir_end = normalize_wedge_spans(*IR_SPANS["T3"])
    remaining_gene = {**get_genes_no_introns("T3", gene_data)[-1], "start": t3_ir_end}
    remaining_width = get_width(remaining_gene, InnerR)
    col_starts.append(col_starts[-1] + col_widths[-1] + linear_gap)
    col_widths.append(remaining_width)
    rows[2][0].append(
        {
            "x": panel_x0 + col_starts[-1],
            "w": remaining_width,
            "color": remaining_gene["color"],
        }
    )

    # Dotted lines per column
    for row, y in rows:
        for entry, col_w in zip(row, col_widths):
            dotted_line(ax, entry["x"], y, entry["x"] + col_w, y, lw=1.0)

    # Row labels
    label_x = panel_x0 - 0.5
    for i, (label, y) in enumerate(zip(["T1", "T2", "T3"], y_positions)):
        ax.text(label_x, y, label, ha="right", va="center", fontsize=LABEL_FONTSIZE)

    # Bars
    gene_arrows = []
    for row, y in rows:
        for entry in row:
            gene_arrows.append(
                draw_gene_arrow(ax, entry["x"], y, entry["w"], box_h, entry["color"])
            )

    x_max = panel_x0 + col_starts[-1] + col_widths[-1]
    y_min = min(y_positions) - box_h / 2.0
    y_max = max(header_y, max(y_positions) + box_h / 2.0)
    return {"x_max": x_max, "y_min": y_min, "y_max": y_max, "gene_arrows": gene_arrows}


def alignment_introns(
    ax, InnerR, gene_data, panel_x0, box_h, base_y, row_spacing, header_offset=0.9
):
    """Display only introns in gene-wise columns."""
    linear_gap = SPLIT_ALIGNMENT_GAP_STRETCH * (10.0 / 180.0) * np.pi * InnerR

    # Get introns only
    def get_introns_only(genome_key):
        return [elem for elem in gene_data[genome_key] if elem.get("type") == "intron"]

    introns_by_genome = {g: get_introns_only(g) for g in ["T1", "T2", "T3"]}
    intron_count = len(introns_by_genome["T1"])

    if intron_count == 0:
        return {"x_max": panel_x0, "y_min": base_y, "y_max": base_y}

    # Column widths: max width for each intron across genomes
    col_widths = []
    for i in range(intron_count):
        widths = [
            get_width(introns_by_genome[g][i], InnerR) for g in ["T1", "T2", "T3"]
        ]
        col_widths.append(max(widths))

    # Column start positions
    col_starts = [0.8]
    for i in range(intron_count - 1):
        col_starts.append(col_starts[-1] + col_widths[i] + linear_gap)

    header_y = base_y + header_offset

    y_positions = [base_y + i * row_spacing for i in range(3)]

    def build_row(genome_key):
        introns = introns_by_genome[genome_key]
        result = []
        for i in range(intron_count):
            intron = introns[i]
            result.append(
                {
                    "x": panel_x0 + col_starts[i],
                    "w": get_width(intron, InnerR),
                    "color": intron["color"],
                }
            )
        return result

    rows = [
        (build_row("T1"), y_positions[0]),
        (build_row("T2"), y_positions[1]),
        (build_row("T3"), y_positions[2]),
    ]

    # Dotted lines per column
    for row, y in rows:
        for entry, col_w in zip(row, col_widths):
            dotted_line(ax, entry["x"], y, entry["x"] + col_w, y, lw=1.0)

    # Row labels
    label_x = panel_x0 - 0.5
    for i, (label, y) in enumerate(zip(["T1", "T2", "T3"], y_positions)):
        ax.text(label_x, y, label, ha="right", va="center", fontsize=LABEL_FONTSIZE)

    # Bars
    for row, y in rows:
        for entry in row:
            draw_box(
                ax, entry["x"], y, entry["w"], box_h, entry["color"], is_intron=True
            )

    x_max = panel_x0 + col_starts[-1] + col_widths[-1]
    y_min = min(y_positions) - box_h / 2.0
    y_max = max(header_y, max(y_positions) + box_h / 2.0)
    return {"x_max": x_max, "y_min": y_min, "y_max": y_max}


def alignment_IGS(
    ax, InnerR, gene_data, panel_x0, box_h, base_y, row_spacing, header_offset=0.9
):
    """Display only intergenic spacers (IGS) in gene-wise columns with two-color striped pattern."""
    linear_gap = SPLIT_ALIGNMENT_GAP_STRETCH * (10.0 / 180.0) * np.pi * InnerR

    # Get IGS only and their flanking gene colors
    def get_IGS_with_flanking_colors(genome_key):
        genome_elements = gene_data[genome_key]
        igs_list = []

        for element_idx, elem in enumerate(genome_elements):
            if elem.get("type") == "IGS":
                # Find flanking gene colors using helper function
                prev_gene_color, next_gene_color = find_flanking_gene_colors(
                    genome_elements, element_idx
                )

                igs_list.append(
                    {
                        **elem,
                        "prev_color": prev_gene_color,
                        "next_color": next_gene_color,
                    }
                )

        # Exclude the initial IGS from the extracted-spacer alignment.
        return igs_list[1:]

    igs_by_genome = {g: get_IGS_with_flanking_colors(g) for g in ["T1", "T2", "T3"]}
    igs_count = len(igs_by_genome["T1"])

    if igs_count == 0:
        return {"x_max": panel_x0, "y_min": base_y, "y_max": base_y}

    for genome, igs_list in igs_by_genome.items():
        _, _, ir_start, _ = normalize_wedge_spans(*IR_SPANS[genome])
        second_repeat_igs = igs_list[-2]
        second_repeat_igs["end"] = max(
            second_repeat_igs["start"], min(second_repeat_igs["end"], ir_start)
        )
    if all(
        igs_list[-2]["start"] == igs_list[-2]["end"]
        for igs_list in igs_by_genome.values()
    ):
        for igs_list in igs_by_genome.values():
            del igs_list[-2]
        igs_count -= 1

    # Column widths: max width for each IGS across genomes
    col_widths = []
    for i in range(igs_count):
        widths = [get_width(igs_by_genome[g][i], InnerR) for g in ["T1", "T2", "T3"]]
        col_widths.append(max(widths))

    # Column start positions
    col_starts = [0.8]
    for i in range(igs_count - 1):
        col_starts.append(col_starts[-1] + col_widths[i] + linear_gap)

    header_y = base_y + header_offset

    y_positions = [base_y + i * row_spacing for i in range(3)]

    def build_row(genome_key):
        igs_list = igs_by_genome[genome_key]
        result = []
        for i in range(igs_count):
            igs = igs_list[i]
            result.append(
                {
                    "x": panel_x0 + col_starts[i],
                    "w": get_width(igs, InnerR),
                    "prev_color": igs.get("prev_color"),
                    "next_color": igs.get("next_color"),
                }
            )
        return result

    rows = [
        (build_row("T1"), y_positions[0]),
        (build_row("T2"), y_positions[1]),
        (build_row("T3"), y_positions[2]),
    ]

    # Dotted lines per column
    for row, y in rows:
        for entry, col_w in zip(row, col_widths):
            if entry["w"] > 0:
                dotted_line(ax, entry["x"], y, entry["x"] + col_w, y, lw=1.0)

    # Row labels
    label_x = panel_x0 - 0.5
    for i, (label, y) in enumerate(zip(["T1", "T2", "T3"], y_positions)):
        ax.text(label_x, y, label, ha="right", va="center", fontsize=LABEL_FONTSIZE)

    # Bars with striped pattern
    for row, y in rows:
        for entry in row:
            if entry["w"] == 0:
                continue
            if entry["prev_color"] and entry["next_color"]:
                draw_striped_box(
                    ax,
                    entry["x"],
                    y,
                    entry["w"],
                    box_h,
                    entry["prev_color"],
                    entry["next_color"],
                )
            else:
                draw_box(ax, entry["x"], y, entry["w"], box_h, "gray")

    x_max = panel_x0 + col_starts[-1] + col_widths[-1]
    y_min = min(y_positions) - box_h / 2.0
    y_max = max(header_y, max(y_positions) + box_h / 2.0)
    return {"x_max": x_max, "y_min": y_min, "y_max": y_max}


def alignment_unsplit(
    ax,
    InnerR,
    gene_data,
    panel_x0,
    panel_left_guide_x,
    box_h,
    base_y,
    row_spacing,
    header_offset=0.9,
):
    """Unsplit alignment: genes laid out sequentially per genome with shared dotted baselines."""
    linear_gap = (10.0 / 180.0) * np.pi * InnerR

    def get_group_width(item):
        if isinstance(item, list):
            return sum(get_width(seg, InnerR) for seg in item)
        else:
            return get_width(item, InnerR)

    def compute_positions(genome_key):
        genes = group_gene_segments(genome_key, gene_data)
        positions = [0.8]
        for i in range(len(genes) - 1):
            positions.append(positions[-1] + get_group_width(genes[i]) + linear_gap)
        return positions

    positions_by_genome = {
        "T1": compute_positions("T1"),
        "T2": compute_positions("T2"),
        "T3": compute_positions("T3"),
    }

    genes_by_genome = {g: group_gene_segments(g, gene_data) for g in ["T1", "T2", "T3"]}
    header_y = base_y + header_offset

    def build_row(genome_key):
        genes = genes_by_genome[genome_key]
        positions = positions_by_genome[genome_key]
        result = []
        for i in range(len(genes)):
            item = genes[i]
            if isinstance(item, list):
                # Group of segments
                segments = []
                x_offset = 0
                for seg in item:
                    segments.append(
                        {
                            "x": panel_x0 + positions[i] + x_offset,
                            "w": get_width(seg, InnerR),
                            "color": seg["color"],
                            "is_intron": seg.get("type") == "intron",
                        }
                    )
                    x_offset += get_width(seg, InnerR)
                result.append({"segments": segments})
            else:
                result.append(
                    {
                        "segments": [
                            {
                                "x": panel_x0 + positions[i],
                                "w": get_width(item, InnerR),
                                "color": item["color"],
                                "is_intron": item.get("type") == "intron",
                            }
                        ]
                    }
                )
        return result

    y_positions = [base_y + i * row_spacing for i in range(3)]
    rows = [
        (build_row("T1"), y_positions[0]),
        (build_row("T2"), y_positions[1]),
        (build_row("T3"), y_positions[2]),
    ]

    # Dotted baselines per row (shorter lead-in)
    def get_row_max_x(row):
        last_entry = row[-1]
        last_seg = last_entry["segments"][-1]
        return last_seg["x"] + last_seg["w"]

    row_max_x = max(get_row_max_x(r) for r, _ in rows)
    lead_start = panel_x0 + 0.6
    for row, y in rows:
        dotted_line(ax, lead_start, y, row_max_x, y, lw=1.0)

    # Row labels
    label_x = panel_x0 - 0.5
    for i, (label, y) in enumerate(zip(["T1", "T2", "T3"], y_positions)):
        ax.text(label_x, y, label, ha="right", va="center", fontsize=LABEL_FONTSIZE)

    # Bars - draw all segments
    gene_arrows = []
    for row, y in rows:
        for entry in row:
            for seg in entry["segments"]:
                is_intron = seg.get("is_intron", False)
                if is_intron:
                    draw_box(
                        ax, seg["x"], y, seg["w"], box_h, seg["color"], is_intron=True
                    )
                else:
                    gene_arrows.append(
                        draw_gene_arrow(ax, seg["x"], y, seg["w"], box_h, seg["color"])
                    )

    y_min = min(y_positions) - box_h / 2.0
    y_max = max(header_y, max(y_positions) + box_h / 2.0)
    return {
        "x_max": row_max_x,
        "y_min": y_min,
        "y_max": y_max,
        "gene_arrows": gene_arrows,
    }


# ---------------------------
# Draw bracket between panels
# ---------------------------


def draw_bracket(ax, centers, R, right_panel_left, tick_width=0.5, lw=2):
    """Draw a vertical bracket between the left and right panels.

    The bracket spans from the top edge of the top circle to the bottom edge of the bottom circle.
    """
    bracket_x = (LEFT_PANEL_RIGHT + right_panel_left) / 2.0
    # top edge of top circle (centers[0]) and bottom edge of bottom circle (centers[2])
    bracket_top = centers[0][1] + R
    bracket_bottom = centers[2][1] - R
    bracket_mid = (bracket_top + bracket_bottom) / 2.0

    ax.plot([bracket_x, bracket_x], [bracket_bottom, bracket_top], color="black", lw=lw)
    ax.plot(
        [bracket_x - tick_width, bracket_x],
        [bracket_top, bracket_top],
        color="black",
        lw=lw,
    )
    ax.plot(
        [bracket_x - tick_width, bracket_x],
        [bracket_bottom, bracket_bottom],
        color="black",
        lw=lw,
    )
    # Mid tick pointing right to mimic a brace
    ax.plot(
        [bracket_x, bracket_x + tick_width / 2],
        [bracket_mid, bracket_mid],
        color="black",
        lw=lw,
    )


# ---------------------------
# Main
# ---------------------------


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create Figure 2 method overview and export PNG, SVG, and PDF files."
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory for image files (default: script directory).",
    )
    parser.add_argument(
        "--output-name",
        help="Output filename (with or without extension); script writes PNG, SVG, and PDF.",
    )
    parser.add_argument(
        "--output-prefix",
        help="Output path with or without extension; a date suffix is added.",
    )
    args = parser.parse_args()
    if args.output_prefix is not None:
        if args.output_dir is not None or args.output_name is not None:
            parser.error("--output-prefix cannot be combined with --output-dir or --output-name")
        args.output_dir = os.path.dirname(args.output_prefix) or "."
        args.output_name = os.path.basename(args.output_prefix)
        if not args.output_name:
            parser.error("--output-prefix must include a filename")
    elif args.output_name is None:
        args.output_name = "Figure2_MethodOverview"
    return args


def resolve_output_paths(output_dir, output_name):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target_dir = output_dir if output_dir else script_dir
    os.makedirs(target_dir, exist_ok=True)
    output_base = f"{os.path.splitext(output_name)[0]}__{date.today():%Y_%m_%d}"
    return (
        os.path.join(target_dir, f"{output_base}.svg"),
        os.path.join(target_dir, f"{output_base}.png"),
        os.path.join(target_dir, f"{output_base}.pdf"),
    )


def main():
    args = parse_args()
    svg_path, png_path, pdf_path = resolve_output_paths(args.output_dir, args.output_name)

    fig, ax = plt.subplots(figsize=(16, 8))
    ax.set_aspect("equal")
    ax.axis("off")

    # Okabe-Ito (colorblind safe) excluding vermillion and black
    col_orange = (230 / 255, 159 / 255, 0 / 255)  # orange
    col_skyblue = (86 / 255, 180 / 255, 233 / 255)  # sky blue
    col_green = (0 / 255, 158 / 255, 115 / 255)  # bluish green
    col_yellow = (240 / 255, 228 / 255, 66 / 255)  # yellow
    col_blue = (0 / 255, 114 / 255, 178 / 255)  # blue
    col_purple = (204 / 255, 121 / 255, 167 / 255)  # reddish purple
    col_beige = (245 / 255, 222 / 255, 179 / 255)  # beige/wheat

    R = 5.3
    InnerR = 4.6

    gene_data = {
        "T1": [
            {"type": "IGS", "start": 0, "end": 3},
            {"type": "gene", "color": col_orange, "start": 3, "end": 27},
            {"type": "IGS", "start": 27, "end": 35},
            {
                "type": "gene",
                "color": col_skyblue,
                "start": 35,
                "end": 58,
                "clockwise": True,
            },
            {"type": "IGS", "start": 58, "end": 76},
            {
                "type": "gene",
                "color": col_green,
                "start": 76,
                "end": 89,
                "merge_next_cds": True,
            },
            {"type": "intron", "color": col_green, "start": 89, "end": 97},
            {"type": "gene", "color": col_green, "start": 97, "end": 115},
            {"type": "IGS", "start": 115, "end": 124},
            {"type": "gene", "color": col_yellow, "start": 124, "end": 167},
            {"type": "IGS", "start": 167, "end": 189},
            {
                "type": "gene",
                "color": col_purple,
                "start": 189,
                "end": 195,
                "merge_next_cds": True,
            },
            {"type": "intron", "color": col_purple, "start": 195, "end": 197},
            {
                "type": "gene",
                "color": col_purple,
                "start": 197,
                "end": 202,
                "clockwise": True,
            },
            {"type": "IGS", "start": 202, "end": 217},
            {"type": "gene", "color": col_blue, "start": 217, "end": 236},
            {"type": "IGS", "start": 236, "end": 260},
            {"type": "gene", "color": col_beige, "start": 260, "end": 280},
            {"type": "IGS", "start": 280, "end": 298},
            {
                "type": "gene",
                "color": col_blue,
                "start": 298,
                "end": 323,
                "clockwise": True,
            },
            {"type": "IGS", "start": 323, "end": 360},
        ],
        "T2": [
            {"type": "IGS", "start": 0, "end": 5},
            {"type": "gene", "color": col_orange, "start": 5, "end": 23},
            {"type": "IGS", "start": 23, "end": 40},
            {
                "type": "gene",
                "color": col_skyblue,
                "start": 40,
                "end": 55,
                "clockwise": True,
            },
            {"type": "IGS", "start": 55, "end": 83},
            {
                "type": "gene",
                "color": col_green,
                "start": 83,
                "end": 94,
                "merge_next_cds": True,
            },
            {"type": "intron", "color": col_green, "start": 94, "end": 98},
            {"type": "gene", "color": col_green, "start": 98, "end": 105},
            {"type": "IGS", "start": 105, "end": 120},
            {"type": "gene", "color": col_yellow, "start": 120, "end": 155},
            {"type": "IGS", "start": 155, "end": 170},
            {
                "type": "gene",
                "color": col_purple,
                "start": 170,
                "end": 181,
                "merge_next_cds": True,
            },
            {"type": "intron", "color": col_purple, "start": 181, "end": 193},
            {
                "type": "gene",
                "color": col_purple,
                "start": 193,
                "end": 202,
                "clockwise": True,
            },
            {"type": "IGS", "start": 202, "end": 217},
            {"type": "gene", "color": col_blue, "start": 217, "end": 245},
            {"type": "IGS", "start": 245, "end": 261},
            {"type": "gene", "color": col_beige, "start": 261, "end": 279},
            {"type": "IGS", "start": 279, "end": 295},
            {
                "type": "gene",
                "color": col_blue,
                "start": 295,
                "end": 323,
                "clockwise": True,
            },
            {"type": "IGS", "start": 323, "end": 360},
        ],
        "T3": [
            {"type": "IGS", "start": 0, "end": 2},
            {"type": "gene", "color": col_orange, "start": 2, "end": 23},
            {"type": "IGS", "start": 23, "end": 38},
            {
                "type": "gene",
                "color": col_skyblue,
                "start": 38,
                "end": 53,
                "clockwise": True,
            },
            {"type": "IGS", "start": 53, "end": 72},
            {
                "type": "gene",
                "color": col_green,
                "start": 72,
                "end": 85,
                "merge_next_cds": True,
            },
            {"type": "intron", "color": col_green, "start": 85, "end": 97},
            {"type": "gene", "color": col_green, "start": 97, "end": 109},
            {"type": "IGS", "start": 109, "end": 131},
            {"type": "gene", "color": col_yellow, "start": 131, "end": 159},
            {"type": "IGS", "start": 159, "end": 175},
            {
                "type": "gene",
                "color": col_purple,
                "start": 175,
                "end": 184,
                "merge_next_cds": True,
            },
            {"type": "intron", "color": col_purple, "start": 184, "end": 187},
            {
                "type": "gene",
                "color": col_purple,
                "start": 187,
                "end": 197,
                "clockwise": True,
            },
            {"type": "IGS", "start": 197, "end": 211},
            {"type": "gene", "color": col_blue, "start": 211, "end": 245},
            {"type": "IGS", "start": 245, "end": 261},
            {"type": "gene", "color": col_beige, "start": 261, "end": 276},
            {"type": "IGS", "start": 276, "end": 292},
            {
                "type": "gene",
                "color": col_blue,
                "start": 292,
                "end": 326,
                "clockwise": True,
            },
            {"type": "IGS", "start": 326, "end": 360},
        ],
    }

    panel_x0 = 11.5
    content_shift = 2.0
    alignment_x0 = panel_x0 + content_shift
    box_h = 0.7
    panel_left_guide_x = panel_x0 - 1.8

    centers, circular_gene_arrows = draw_left_panel(
        ax, gene_data, R, InnerR, igs_width=box_h
    )

    # Right-side panels (stacked, expanding downwards)
    unsplit_base_y = 20.5
    genewise_base_y = 10.81
    introns_base_y = 2.83
    igs_base_y = -5.16
    row_spacing = -1.5

    unsplit_ext = alignment_unsplit(
        ax,
        InnerR,
        gene_data,
        alignment_x0,
        panel_left_guide_x,
        box_h,
        base_y=unsplit_base_y,
        row_spacing=row_spacing,
    )
    genewise_ext = alignment_genewise(
        ax,
        InnerR,
        gene_data,
        alignment_x0,
        box_h,
        base_y=genewise_base_y,
        row_spacing=row_spacing,
    )
    introns_ext = alignment_introns(
        ax,
        InnerR,
        gene_data,
        alignment_x0,
        box_h,
        base_y=introns_base_y,
        row_spacing=row_spacing,
    )
    igs_ext = alignment_IGS(
        ax,
        InnerR,
        gene_data,
        alignment_x0,
        box_h,
        base_y=igs_base_y,
        row_spacing=row_spacing,
    )

    c_left = panel_left_guide_x - 1.2
    c_bottom = centers[-1][1] - R - 1.0
    c_top = 15.0
    b_bottom = c_top + 1.0
    b_top = centers[0][1] + R + 1.0
    panel_right = LEFT_PANEL_LEFT + 2 * (b_top - c_bottom)
    ax.add_patch(
        Rectangle(
            (c_left, b_bottom),
            panel_right - c_left,
            b_top - b_bottom,
            facecolor="#f2f2f2",
            edgecolor="none",
            zorder=-10,
        )
    )
    ax.text(
        c_left + 0.6,
        b_top - 0.7,
        "B",
        ha="left",
        va="top",
        fontsize=PANEL_LABEL_FONTSIZE,
        fontweight="bold",
        zorder=20,
    )
    ax.add_patch(
        Rectangle(
            (c_left, c_bottom),
            panel_right - c_left,
            c_top - c_bottom,
            facecolor="#f2f2f2",
            edgecolor="none",
            zorder=-10,
        )
    )
    ax.text(
        c_left + 0.6,
        c_top - 0.7,
        "C",
        ha="left",
        va="top",
        fontsize=PANEL_LABEL_FONTSIZE,
        fontweight="bold",
        zorder=20,
    )

    # Optional labels for clarity
    label_x = alignment_x0 - 0.5
    long_labels = [
        ax.text(
            label_x,
            unsplit_base_y + 1.9,
            "Whole genome",
            fontsize=LABEL_FONTSIZE,
            fontstyle="italic",
            ha="left",
            va="center",
        ),
        ax.text(
            label_x,
            genewise_base_y + 1.9,
            "Extracted genes (CDS)",
            fontsize=LABEL_FONTSIZE,
            fontstyle="italic",
            ha="left",
            va="center",
        ),
        ax.text(
            label_x,
            introns_base_y + 1.9,
            "Extracted introns (INT)",
            fontsize=LABEL_FONTSIZE,
            fontstyle="italic",
            ha="left",
            va="center",
        ),
        ax.text(
            label_x,
            igs_base_y + 1.9,
            "Extracted spacer (IGS)",
            fontsize=LABEL_FONTSIZE,
            fontstyle="italic",
            ha="left",
            va="center",
        ),
    ]

    draw_bracket(ax, centers, R, c_left)

    max_x = panel_right + 2.0
    min_y = (
        min(
            centers[2][1] - R,
            genewise_ext["y_min"],
            introns_ext["y_min"],
            unsplit_ext["y_min"],
            igs_ext["y_min"],
        )
        - 2.0
    )
    max_y = (
        max(
            centers[0][1] + R,
            genewise_ext["y_max"],
            introns_ext["y_max"],
            unsplit_ext["y_max"],
            igs_ext["y_max"],
        )
        + 2.0
    )
    ax.set_xlim(-10, max_x)
    ax.set_ylim(min_y, max_y)
    plt.tight_layout(pad=1.0)

    fig.canvas.draw()
    # Match the outlined CDS arc thickness in physical units after layout.
    pixels_per_data_unit = (
        ax.transData.transform((0, 1))[1] - ax.transData.transform((0, 0))[1]
    )
    gene_bar_height = (
        (GENE_ARC_LINEWIDTH + ARC_OUTLINE_EXTRA_WIDTH - BAR_OUTLINE_LINEWIDTH)
        * fig.dpi
        / (72 * pixels_per_data_unit)
    )
    for arrow in unsplit_ext["gene_arrows"] + genewise_ext["gene_arrows"]:
        vertices = arrow.get_xy()
        x, y = vertices[0, 0], vertices[2, 1]
        width = vertices[2, 0] - x
        arrow.set_xy(linear_gene_vertices(x, y, width, gene_bar_height))
    for arrow, center, radius, start, end, clockwise in circular_gene_arrows:
        arrow.set_xy(
            circular_gene_vertices(
                center, radius, start, end, gene_bar_height, clockwise
            )
        )

    taxon_label = next(
        text
        for text in ax.texts
        if text.get_text() == "T1" and text.get_position()[0] == label_x
    )
    taxon_left = taxon_label.get_window_extent(fig.canvas.get_renderer()).x0
    long_label_x = ax.transData.inverted().transform((taxon_left, 0))[0]
    for label in long_labels:
        label.set_x(long_label_x)

    plt.savefig(svg_path, format="svg", dpi=300)
    plt.savefig(png_path, format="png", dpi=300)
    plt.savefig(pdf_path, format="pdf", dpi=300)
    plt.close(fig)
    try:
        location = os.path.relpath(os.path.dirname(svg_path))
    except ValueError:
        location = f"{os.path.abspath(os.path.dirname(svg_path))} (absolute path; relative path unavailable)"
    print(f"Wrote files to {location}")


if __name__ == "__main__":
    main()

# Make the genes considerably shorter and longer
# Display the scenario if a gene is missing from one of the genomes
# Display the scenario where one gene overlaps with another
# Add the IRs
# Display the situation that a gene is duplicated by the IR
