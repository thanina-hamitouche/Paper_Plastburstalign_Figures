import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Arc, Rectangle, Wedge
import os
import argparse

# ---------------------------
# Helper functions
# ---------------------------
def polar_to_cart(r, theta_deg):
    theta = np.deg2rad(theta_deg)
    return r * np.cos(theta), r * np.sin(theta)

def draw_arc(ax, center, r, start, end, color, lw=4, alpha=0.95, hatch=None, fill=False, edgecolor=None, add_outline=False):
    cx, cy = center
    
    # Add thin black outline underneath if requested (draw first so it's behind)
    if add_outline:
        outline_arc = Arc((cx, cy),
                         width=2*r, height=2*r,
                         theta1=start, theta2=end,
                         color='black', lw=lw + 1, alpha=1.0)
        ax.add_patch(outline_arc)
        
        # Add radial lines at start and end of arc (the "sides")
        # Arc thickness in data units (rough approximation based on linewidth)
        thickness_offset = lw * 0.026  # Adjust this factor to match visual arc thickness
        inner_r = r - thickness_offset
        outer_r = r + thickness_offset
        
        # Start edge
        x1_start, y1_start = polar_to_cart(inner_r, start)
        x2_start, y2_start = polar_to_cart(outer_r, start)
        ax.plot([cx + x1_start, cx + x2_start], [cy + y1_start, cy + y2_start], 
                color='black', lw=0.5, solid_capstyle='butt')
        
        # End edge
        x1_end, y1_end = polar_to_cart(inner_r, end)
        x2_end, y2_end = polar_to_cart(outer_r, end)
        ax.plot([cx + x1_end, cx + x2_end], [cy + y1_end, cy + y2_end], 
                color='black', lw=0.5, solid_capstyle='butt')
    
    if fill:
        # For filled arc with hatching
        arc = Arc((cx, cy),
                  width=2*r, height=2*r,
                  theta1=start, theta2=end,
                  color=edgecolor if edgecolor else color, lw=lw, alpha=alpha,
                  fill=False, hatch=hatch)
    else:
        arc = Arc((cx, cy),
                  width=2*r, height=2*r,
                  theta1=start, theta2=end,
                  color=color, lw=lw, alpha=alpha)
    ax.add_patch(arc)

def draw_hatched_arc(ax, center, r, start, end, color1, color2, lw=8):
    """Draw a thick arc with slanted ribbon pattern showing two colors."""
    cx, cy = center
    width = 0.4  # Width of the arc band
    
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
        
        wedge = Wedge(center, r + width/2, segment_start, segment_end, width=width,
                     facecolor=color, edgecolor=color, alpha=0.9, linewidth=0)
        ax.add_patch(wedge)
    
    # Handle remaining partial segment if any
    remaining = arc_span - (num_segments * segment_size)
    if remaining > 0.5:  # Only draw if significant
        segment_start = start + num_segments * segment_size
        segment_end = end
        color = color1 if num_segments % 2 == 0 else color2
        wedge = Wedge(center, r + width/2, segment_start, segment_end, width=width,
                     facecolor=color, edgecolor=color, alpha=0.9, linewidth=0)
        ax.add_patch(wedge)
    
    # Add black outline around entire striped arc
    outline_outer = Arc((cx, cy), width=2*(r + width/2), height=2*(r + width/2),
                       theta1=start, theta2=end, color='black', lw=0.5, alpha=1.0)
    ax.add_patch(outline_outer)
    outline_inner = Arc((cx, cy), width=2*(r - width/2), height=2*(r - width/2),
                       theta1=start, theta2=end, color='black', lw=0.5, alpha=1.0)
    ax.add_patch(outline_inner)
    
    # Add radial end caps at start and end of arc
    inner_r = r - width/2
    outer_r = r + width/2
    
    # Start edge
    x1_start, y1_start = polar_to_cart(inner_r, start)
    x2_start, y2_start = polar_to_cart(outer_r, start)
    ax.plot([cx + x1_start, cx + x2_start], [cy + y1_start, cy + y2_start], 
            color='black', lw=0.5, solid_capstyle='butt')
    
    # End edge
    x1_end, y1_end = polar_to_cart(inner_r, end)
    x2_end, y2_end = polar_to_cart(outer_r, end)
    ax.plot([cx + x1_end, cx + x2_end], [cy + y1_end, cy + y2_end], 
            color='black', lw=0.5, solid_capstyle='butt')

def dotted_line(ax, x1, y1, x2, y2, dotsize=4, lw=1.0, zorder=0):
    xs = np.linspace(x1, x2, 40)
    ys = np.linspace(y1, y2, 40)
    ax.plot(xs, ys, linestyle=':', color='black', linewidth=lw, zorder=zorder)

def draw_box(ax, x, y_center, w, h, color, is_intron=False):
    rect_h = h / 2.0 if is_intron else h
    rect = Rectangle((x, y_center - rect_h/2), w, rect_h, fill=True, facecolor=color, 
                     edgecolor='black', linewidth=0.5, zorder=2)
    ax.add_patch(rect)

def draw_striped_box(ax, x, y_center, w, h, color1, color2):
    """Draw a box with alternating vertical stripes of two colors."""
    segment_width = 0.15  # Fixed stripe width
    num_segments = int(w / segment_width)
    
    for i in range(num_segments):
        stripe_x = x + i * segment_width
        stripe_w = min(segment_width, w - i * segment_width)
        color = color1 if i % 2 == 0 else color2
        
        rect = Rectangle((stripe_x, y_center - h/2), stripe_w, h, 
                        fill=True, facecolor=color, lw=0, zorder=2, alpha=0.9)
        ax.add_patch(rect)
    
    # Handle remaining partial stripe
    remaining = w - (num_segments * segment_width)
    if remaining > 0.01:
        stripe_x = x + num_segments * segment_width
        color = color1 if num_segments % 2 == 0 else color2
        rect = Rectangle((stripe_x, y_center - h/2), remaining, h, 
                        fill=True, facecolor=color, lw=0, zorder=2, alpha=0.9)
        ax.add_patch(rect)
    
    # Add black outline around entire striped box
    outline = Rectangle((x, y_center - h/2), w, h, fill=False, 
                       edgecolor='black', linewidth=0.5, zorder=3)
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
    ax.plot([cx + x0, cx + x1], [cy + y0, cy + y1], color='black', lw=1.5, zorder=3)
    ax.scatter(cx + xt, cy + yt, marker='^', color='black', s=35, zorder=4)

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
        while next_idx < len(elements) and elements[next_idx].get("color") == current_element.get("color"):
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
        for j in range(0, igs_index):
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

def draw_left_panel(ax, gene_data, R, InnerR):
    """Draw circles with arcs using gene position data (start and end angles)."""
    y_top, spacing = 18.0, -11.0
    centers = [(0, y_top), (0, y_top + spacing), (0, y_top + 2*spacing)]
    labels = ["T₁", "T₂", "T₃"]
    genomes = ["T1", "T2", "T3"]
    
    IGS_R = InnerR - 1.2  # Inner circle for IGS markers (smaller diameter)
    
    for idx, (center, label, genome_key) in enumerate(zip(centers, labels, genomes)):
        # Draw gray background wedges behind genes (draw first so they're in the back)
        if idx == 0:  # T1:
            wedge1_start, wedge1_end = 219.2, 255.8
            wedge2_start, wedge2_end = 284.2, 329.8
        elif idx == 1:  # T2: 
            wedge1_start, wedge1_end = 210, 257
            wedge2_start, wedge2_end = 283, 324
        else:  # T3: 20% reduced span
            wedge1_start, wedge1_end = 219, 251
            wedge2_start, wedge2_end = 289, 321
        
        # Normalize wedge spans to ensure both wedges have equal angular extent
        wedge1_start, wedge1_end, wedge2_start, wedge2_end = normalize_wedge_spans(
            wedge1_start, wedge1_end, wedge2_start, wedge2_end)
        
        gray_wedge1 = Wedge(center, InnerR, to_plot_angle(wedge1_start), to_plot_angle(wedge1_end), 
                           facecolor='lightgray', edgecolor='none', alpha=0.3, zorder=0)
        ax.add_patch(gray_wedge1)
        gray_wedge2 = Wedge(center, InnerR, to_plot_angle(wedge2_start), to_plot_angle(wedge2_end), 
                           facecolor='lightgray', edgecolor='none', alpha=0.3, zorder=0)
        ax.add_patch(gray_wedge2)
        
        # Draw fine black circle at gene/intron radius
        ax.add_patch(plt.Circle(center, InnerR, fill=False, color='black', lw=1))
        # Origin marker at outer radius
        add_origin_marker(ax, center, R, angle_deg=to_plot_angle(0.0))
        
        # Draw IGS markers on inner circle with ribbon pattern from flanking genes
        genome_elements = gene_data[genome_key]
        for element_idx, element in enumerate(genome_elements):
            if element.get("type") == "IGS":
                start_angle = to_plot_angle(element["start"])
                end_angle = to_plot_angle(element["end"])
                
                # Find flanking gene colors
                prev_gene_color, next_gene_color = find_flanking_gene_colors(genome_elements, element_idx)
                
                # Draw with ribbon pattern using both colors
                if prev_gene_color and next_gene_color:
                    draw_hatched_arc(ax, center, IGS_R, start_angle, end_angle, prev_gene_color, next_gene_color, lw=8)
                else:
                    draw_arc(ax, center, IGS_R, start_angle, end_angle, color='gray', lw=8)
        
        # Draw genes and introns
        for element in gene_data[genome_key]:
            start_angle = to_plot_angle(element["start"])
            end_angle = to_plot_angle(element["end"])
            if element.get("type") == "intron":
                # Introns: much thinner than genes
                draw_arc(ax, center, InnerR, start_angle, end_angle, color=element["color"], lw=3, add_outline=True)
            elif element.get("type") == "gene":
                # Thicker arcs to match right-side bar thickness
                draw_arc(ax, center, InnerR, start_angle, end_angle, color=element["color"], lw=14, add_outline=True)
        ax.text(center[0], center[1], label, ha='center', va='center', fontsize=14)
    
    return centers

# ---------------------------
# Right-side panels
# ---------------------------

def alignment_genewise(ax, InnerR, gene_data, panel_x0, box_h, base_y, row_spacing, header_offset=0.9):
    """Gene-wise columns: each gene gets its own column, dotted per column, rows stacked tightly. Introns excluded."""
    linear_gap = (10.0 / 180.0) * np.pi * InnerR

    genes_by_genome = {g: [e for e in get_genes_no_introns(g, gene_data)] for g in ["T1", "T2", "T3"]}
    gene_count = len(genes_by_genome["T1"])

    # Column widths: max width for each gene across genomes
    col_widths = []
    for i in range(gene_count):
        widths = [get_width(genes_by_genome[g][i], InnerR) for g in ["T1", "T2", "T3"]]
        col_widths.append(max(widths))

    # Column start positions
    col_starts = [0.8]
    for i in range(gene_count - 1):
        col_starts.append(col_starts[-1] + col_widths[i] + linear_gap)

    header_y = base_y + header_offset
    headers = ["Gene 1", "Gene 2", "Gene 3", "Gene 4", "Gene 5", "Gene 6", "Gene 7", "Gene 8"]
    for i, h in enumerate(headers[:gene_count]):
        hx = panel_x0 + col_starts[i] + col_widths[i] / 2.0
        ax.text(hx, header_y, h, ha='center', va='center', fontsize=12)

    y_positions = [base_y + i * row_spacing for i in range(3)]

    def build_row(genome_key):
        genes = genes_by_genome[genome_key]
        result = []
        for i in range(gene_count):
            gene = genes[i]
            result.append({
                "x": panel_x0 + col_starts[i],
                "w": get_width(gene, InnerR),
                "color": gene["color"]
            })
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
    for i, (label, y) in enumerate(zip(["T₁", "T₂", "T₃"], y_positions)):
        ax.text(label_x, y, label, ha='right', va='center', fontsize=11)

    # Bars
    for row, y in rows:
        for entry in row:
            draw_box(ax, entry["x"], y, entry["w"], box_h, entry["color"])

    x_max = panel_x0 + col_starts[-1] + col_widths[-1]
    y_min = min(y_positions) - box_h / 2.0
    y_max = max(header_y, max(y_positions) + box_h / 2.0)
    return {"x_max": x_max, "y_min": y_min, "y_max": y_max}


def alignment_introns(ax, InnerR, gene_data, panel_x0, box_h, base_y, row_spacing, header_offset=0.9):
    """Display only introns in gene-wise columns."""
    linear_gap = (10.0 / 180.0) * np.pi * InnerR

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
        widths = [get_width(introns_by_genome[g][i], InnerR) for g in ["T1", "T2", "T3"]]
        col_widths.append(max(widths))

    # Column start positions
    col_starts = [0.8]
    for i in range(intron_count - 1):
        col_starts.append(col_starts[-1] + col_widths[i] + linear_gap)

    header_y = base_y + header_offset
    headers = ["Intron 1", "Intron 2", "Intron 3", "Intron 4"]
    for i, h in enumerate(headers[:intron_count]):
        hx = panel_x0 + col_starts[i] + col_widths[i] / 2.0
        ax.text(hx, header_y, h, ha='center', va='center', fontsize=12)

    y_positions = [base_y + i * row_spacing for i in range(3)]

    def build_row(genome_key):
        introns = introns_by_genome[genome_key]
        result = []
        for i in range(intron_count):
            intron = introns[i]
            result.append({
                "x": panel_x0 + col_starts[i],
                "w": get_width(intron, InnerR),
                "color": intron["color"]
            })
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
    for i, (label, y) in enumerate(zip(["T₁", "T₂", "T₃"], y_positions)):
        ax.text(label_x, y, label, ha='right', va='center', fontsize=11)

    # Bars
    for row, y in rows:
        for entry in row:
            draw_box(ax, entry["x"], y, entry["w"], box_h, entry["color"], is_intron=True)

    x_max = panel_x0 + col_starts[-1] + col_widths[-1]
    y_min = min(y_positions) - box_h / 2.0
    y_max = max(header_y, max(y_positions) + box_h / 2.0)
    return {"x_max": x_max, "y_min": y_min, "y_max": y_max}


def alignment_IGS(ax, InnerR, gene_data, panel_x0, box_h, base_y, row_spacing, header_offset=0.9):
    """Display only intergenic spacers (IGS) in gene-wise columns with two-color striped pattern."""
    linear_gap = (10.0 / 180.0) * np.pi * InnerR

    # Get IGS only and their flanking gene colors
    def get_IGS_with_flanking_colors(genome_key):
        genome_elements = gene_data[genome_key]
        igs_list = []
        
        for element_idx, elem in enumerate(genome_elements):
            if elem.get("type") == "IGS":
                # Find flanking gene colors using helper function
                prev_gene_color, next_gene_color = find_flanking_gene_colors(genome_elements, element_idx)
                
                igs_list.append({
                    **elem,
                    "prev_color": prev_gene_color,
                    "next_color": next_gene_color
                })
        
        return igs_list
    
    igs_by_genome = {g: get_IGS_with_flanking_colors(g) for g in ["T1", "T2", "T3"]}
    igs_count = len(igs_by_genome["T1"])
    
    if igs_count == 0:
        return {"x_max": panel_x0, "y_min": base_y, "y_max": base_y}

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
    headers = ["IGS 1", "IGS 2", "IGS 3", "IGS 4", "IGS 5", "IGS 6", "IGS 7"]
    for i, h in enumerate(headers[:igs_count]):
        hx = panel_x0 + col_starts[i] + col_widths[i] / 2.0
        ax.text(hx, header_y, h, ha='center', va='center', fontsize=12)

    y_positions = [base_y + i * row_spacing for i in range(3)]

    def build_row(genome_key):
        igs_list = igs_by_genome[genome_key]
        result = []
        for i in range(igs_count):
            igs = igs_list[i]
            result.append({
                "x": panel_x0 + col_starts[i],
                "w": get_width(igs, InnerR),
                "prev_color": igs.get("prev_color"),
                "next_color": igs.get("next_color")
            })
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
    for i, (label, y) in enumerate(zip(["T₁", "T₂", "T₃"], y_positions)):
        ax.text(label_x, y, label, ha='right', va='center', fontsize=11)

    # Bars with striped pattern
    for row, y in rows:
        for entry in row:
            if entry["prev_color"] and entry["next_color"]:
                draw_striped_box(ax, entry["x"], y, entry["w"], box_h, 
                               entry["prev_color"], entry["next_color"])
            else:
                draw_box(ax, entry["x"], y, entry["w"], box_h, 'gray')

    x_max = panel_x0 + col_starts[-1] + col_widths[-1]
    y_min = min(y_positions) - box_h / 2.0
    y_max = max(header_y, max(y_positions) + box_h / 2.0)
    return {"x_max": x_max, "y_min": y_min, "y_max": y_max}


def alignment_unsplit(ax, InnerR, gene_data, panel_x0, panel_left_guide_x, box_h, base_y, row_spacing, header_offset=0.9):
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
    headers = ["Gene 1", "Gene 2", "Gene 3", "Gene 4", "Gene 5", "Gene 6", "Gene 7", "Gene 8"]
    header_y = base_y + header_offset

    # Header centers based on T1 layout
    genes_T1 = genes_by_genome["T1"]
    for i, h in enumerate(headers[:len(genes_T1)]):
        hx = panel_x0 + 0.8 + sum(get_group_width(genes_T1[j]) for j in range(i)) + get_group_width(genes_T1[i]) / 2.0
        ax.text(hx, header_y, h, ha='center', va='center', fontsize=12)

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
                    segments.append({
                        "x": panel_x0 + positions[i] + x_offset,
                        "w": get_width(seg, InnerR),
                        "color": seg["color"],
                        "is_intron": seg.get("type") == "intron"
                    })
                    x_offset += get_width(seg, InnerR)
                result.append({"segments": segments})
            else:
                result.append({
                    "segments": [{
                        "x": panel_x0 + positions[i],
                        "w": get_width(item, InnerR),
                        "color": item["color"],
                        "is_intron": item.get("type") == "intron"
                    }]
                })
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
    for i, (label, y) in enumerate(zip(["T₁", "T₂", "T₃"], y_positions)):
        ax.text(label_x, y, label, ha='right', va='center', fontsize=11)

    # Bars - draw all segments
    for row, y in rows:
        for entry in row:
            for seg in entry["segments"]:
                draw_box(ax, seg["x"], y, seg["w"], box_h, seg["color"], seg.get("is_intron", False))

    y_min = min(y_positions) - box_h / 2.0
    y_max = max(header_y, max(y_positions) + box_h / 2.0)
    return {"x_max": row_max_x, "y_min": y_min, "y_max": y_max}

# ---------------------------
# Draw bracket between panels
# ---------------------------

def draw_bracket(ax, centers, R, panel_left_guide_x, tick_width=0.8, lw=2):
    """Draw a vertical bracket halfway between the circle edge (x=R) and the dotted-line guide.

    The bracket spans from the top edge of the top circle to the bottom edge of the bottom circle.
    """
    bracket_x = (panel_left_guide_x + R) / 2.0
    # top edge of top circle (centers[0]) and bottom edge of bottom circle (centers[2])
    bracket_top = centers[0][1] + R
    bracket_bottom = centers[2][1] - R
    bracket_mid = (bracket_top + bracket_bottom) / 2.0

    ax.plot([bracket_x, bracket_x], [bracket_bottom, bracket_top], color="black", lw=lw)
    ax.plot([bracket_x - tick_width, bracket_x], [bracket_top, bracket_top], color="black", lw=lw)
    ax.plot([bracket_x - tick_width, bracket_x], [bracket_bottom, bracket_bottom], color="black", lw=lw)
    # Mid tick pointing right to mimic a brace
    ax.plot([bracket_x, bracket_x + tick_width/2], [bracket_mid, bracket_mid], color="black", lw=lw)


# ---------------------------
# Main
# ---------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Create method overview figure and export both SVG and PNG files."
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory for image files (default: script directory).",
    )
    parser.add_argument(
        "--output-name",
        default="PlastomeBurstAndAlign_Figure1",
        help="Output filename (with or without extension); script writes both .svg and .png.",
    )
    return parser.parse_args()


def resolve_output_paths(output_dir, output_name):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target_dir = output_dir if output_dir else script_dir
    os.makedirs(target_dir, exist_ok=True)
    output_base = os.path.splitext(output_name)[0]
    return (
        os.path.join(target_dir, f"{output_base}.svg"),
        os.path.join(target_dir, f"{output_base}.png"),
    )

def main():
    args = parse_args()
    svg_path, png_path = resolve_output_paths(args.output_dir, args.output_name)

    fig, ax = plt.subplots(figsize=(16, 8))
    ax.set_aspect('equal')
    ax.axis('off')

    # Okabe-Ito (colorblind safe) excluding vermillion and black
    col_orange = (230/255, 159/255, 0/255)     # orange
    col_skyblue = (86/255, 180/255, 233/255)   # sky blue
    col_green = (0/255, 158/255, 115/255)      # bluish green
    col_yellow = (240/255, 228/255, 66/255)    # yellow
    col_blue = (0/255, 114/255, 178/255)       # blue
    col_purple = (204/255, 121/255, 167/255)   # reddish purple
    col_beige = (245/255, 222/255, 179/255)    # beige/wheat

    R = 5.3
    InnerR = 4.6

    gene_data = {
        "T1": [
            {"type": "IGS", "start": 0, "end": 3},
            {"type": "gene", "color": col_orange, "start": 3, "end": 27},
            {"type": "IGS", "start": 27, "end": 35},
            {"type": "gene", "color": col_skyblue, "start": 35, "end": 58},
            {"type": "IGS", "start": 58, "end": 76},
            {"type": "gene", "color": col_green, "start": 76, "end": 89},
            {"type": "intron", "color": col_green, "start": 89, "end": 97},
            {"type": "gene", "color": col_green, "start": 97, "end": 115},
            {"type": "IGS", "start": 115, "end": 124},
            {"type": "gene", "color": col_yellow, "start": 124, "end": 167},
            {"type": "IGS", "start": 167, "end": 189},
            {"type": "gene", "color": col_purple, "start": 189, "end": 195},
            {"type": "intron", "color": col_purple, "start": 195, "end": 197},
            {"type": "gene", "color": col_purple, "start": 197, "end": 202},
            {"type": "IGS", "start": 202, "end": 217},
            {"type": "gene", "color": col_blue, "start": 217, "end": 236},
            {"type": "IGS", "start": 236, "end": 260},
            {"type": "gene", "color": col_beige, "start": 260, "end": 280},
            {"type": "IGS", "start": 280, "end": 298},
            {"type": "gene", "color": col_blue, "start": 298, "end": 323},
            {"type": "IGS", "start": 323, "end": 360},
        ],
        "T2": [
            {"type": "IGS", "start": 0, "end": 5},
            {"type": "gene", "color": col_orange, "start": 5, "end": 23},
            {"type": "IGS", "start": 23, "end": 40},
            {"type": "gene", "color": col_skyblue, "start": 40, "end": 55},
            {"type": "IGS", "start": 55, "end": 83},
            {"type": "gene", "color": col_green, "start": 83, "end": 94},
            {"type": "intron", "color": col_green, "start": 94, "end": 98},
            {"type": "gene", "color": col_green, "start": 98, "end": 105},
            {"type": "IGS", "start": 105, "end": 120},
            {"type": "gene", "color": col_yellow, "start": 120, "end": 155},
            {"type": "IGS", "start": 155, "end": 170},
            {"type": "gene", "color": col_purple, "start": 170, "end": 181},
            {"type": "intron", "color": col_purple, "start": 181, "end": 193},
            {"type": "gene", "color": col_purple, "start": 193, "end": 202},
            {"type": "IGS", "start": 202, "end": 217},
            {"type": "gene", "color": col_blue, "start": 217, "end": 245},
            {"type": "IGS", "start": 245, "end": 261},
            {"type": "gene", "color": col_beige, "start": 261, "end": 279},
            {"type": "IGS", "start": 279, "end": 295},
            {"type": "gene", "color": col_blue, "start": 295, "end": 323},
            {"type": "IGS", "start": 323, "end": 360},
        ],
        "T3": [
            {"type": "IGS", "start": 0, "end": 2},
            {"type": "gene", "color": col_orange, "start": 2, "end": 23},
            {"type": "IGS", "start": 23, "end": 38},
            {"type": "gene", "color": col_skyblue, "start": 38, "end": 53},
            {"type": "IGS", "start": 53, "end": 72},
            {"type": "gene", "color": col_green, "start": 72, "end": 85},
            {"type": "intron", "color": col_green, "start": 85, "end": 97},
            {"type": "gene", "color": col_green, "start": 97, "end": 109},
            {"type": "IGS", "start": 109, "end": 131},
            {"type": "gene", "color": col_yellow, "start": 131, "end": 159},
            {"type": "IGS", "start": 159, "end": 175},
            {"type": "gene", "color": col_purple, "start": 175, "end": 184},
            {"type": "intron", "color": col_purple, "start": 184, "end": 187},
            {"type": "gene", "color": col_purple, "start": 187, "end": 197},
            {"type": "IGS", "start": 197, "end": 211},
            {"type": "gene", "color": col_blue, "start": 211, "end": 245},
            {"type": "IGS", "start": 245, "end": 261},
            {"type": "gene", "color": col_beige, "start": 261, "end": 276},
            {"type": "IGS", "start": 276, "end": 292},
            {"type": "gene", "color": col_blue, "start": 292, "end": 326},
            {"type": "IGS", "start": 326, "end": 360},
        ],
    }

    panel_x0 = 11.5
    box_h = 0.7
    panel_left_guide_x = panel_x0 - 1.8

    centers = draw_left_panel(ax, gene_data, R, InnerR)

    # Right-side panels (stacked, expanding downwards)
    unsplit_base_y = 20.0
    genewise_base_y = 12.01
    introns_base_y = 4.03
    igs_base_y = -3.96
    row_spacing = -1.3  # tight stacking

    unsplit_ext = alignment_unsplit(ax, InnerR, gene_data, panel_x0, panel_left_guide_x, box_h, base_y=unsplit_base_y, row_spacing=row_spacing)
    genewise_ext = alignment_genewise(ax, InnerR, gene_data, panel_x0, box_h, base_y=genewise_base_y, row_spacing=row_spacing)
    introns_ext = alignment_introns(ax, InnerR, gene_data, panel_x0, box_h, base_y=introns_base_y, row_spacing=row_spacing)
    igs_ext = alignment_IGS(ax, InnerR, gene_data, panel_x0, box_h, base_y=igs_base_y, row_spacing=row_spacing)

    # Optional labels for clarity
    ax.text(panel_x0, unsplit_base_y + 1.9, "Unsplit genome alignment", fontsize=12, fontweight='bold', ha='left', va='center')
    ax.text(panel_x0, genewise_base_y + 1.9, "Gene alignments", fontsize=12, fontweight='bold', ha='left', va='center')
    ax.text(panel_x0, introns_base_y + 1.9, "Intron alignments", fontsize=12, fontweight='bold', ha='left', va='center')
    ax.text(panel_x0, igs_base_y + 1.9, "Intergenic spacer alignments", fontsize=12, fontweight='bold', ha='left', va='center')

    draw_bracket(ax, centers, R, panel_left_guide_x)

    max_x = max(genewise_ext["x_max"], introns_ext["x_max"], unsplit_ext["x_max"], igs_ext["x_max"]) + 2.0
    min_y = min(centers[2][1] - R, genewise_ext["y_min"], introns_ext["y_min"], unsplit_ext["y_min"], igs_ext["y_min"]) - 2.0
    max_y = max(centers[0][1] + R, genewise_ext["y_max"], introns_ext["y_max"], unsplit_ext["y_max"], igs_ext["y_max"]) + 2.0
    ax.set_xlim(-10, max_x)
    ax.set_ylim(min_y, max_y)
    plt.tight_layout(pad=1.0)
    
    # Save figure as SVG and PNG.
    plt.savefig(svg_path, format='svg', dpi=300)
    plt.savefig(png_path, format='png', dpi=300)
    plt.close(fig)

if __name__ == "__main__":
    main()

# Make the genes considerably shorter and longer
# Display the scenario if a gene is missing from one of the genomes
# Display the scenario where one gene overlaps with another
# Add the IRs
# Display the situation that a gene is duplicated by the IR
