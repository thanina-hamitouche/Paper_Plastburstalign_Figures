import argparse
import os

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon


def draw_terminator(ax, center, text, width=3.6, height=1.3):
    x, y = center
    patch = FancyBboxPatch(
        (x - width / 2, y - height / 2),
        width,
        height,
        boxstyle="round,pad=0.05,rounding_size=0.2",
        linewidth=1.2,
        edgecolor="black",
        facecolor="white",
        zorder=2,
    )
    ax.add_patch(patch)
    ax.text(x, y, text, ha="center", va="center", fontsize=10, fontweight="bold", zorder=3)


def draw_process(ax, center, text, width=4.2, height=1.3, color="#fff6b3"):
    x, y = center
    patch = FancyBboxPatch(
        (x - width / 2, y - height / 2),
        width,
        height,
        boxstyle="square,pad=0.0",
        linewidth=1.2,
        edgecolor="black",
        facecolor=color,
        zorder=2,
    )
    ax.add_patch(patch)
    ax.text(x, y, text, ha="center", va="center", fontsize=9, zorder=3)


def draw_decision(ax, center, text, width=5.0, height=2.3, color="#cfe8ff"):
    x, y = center
    points = [
        (x, y + height / 2),
        (x + width / 2, y),
        (x, y - height / 2),
        (x - width / 2, y),
    ]
    patch = Polygon(points, closed=True, linewidth=1.2, edgecolor="black", facecolor=color, zorder=2)
    ax.add_patch(patch)
    ax.text(x, y, text, ha="center", va="center", fontsize=8.5, wrap=True, zorder=3)


def draw_data(ax, center, text, width=4.2, height=1.4, color="#ffffff", slope=0.7):
    x, y = center
    points = [
        (x - width / 2 + slope, y + height / 2),
        (x + width / 2, y + height / 2),
        (x + width / 2 - slope, y - height / 2),
        (x - width / 2, y - height / 2),
    ]
    patch = Polygon(points, closed=True, linewidth=1.2, edgecolor="black", facecolor=color, zorder=2)
    ax.add_patch(patch)
    ax.text(x, y, text, ha="center", va="center", fontsize=9, zorder=3)


def draw_connector(ax, points, lw=1.2):
    if len(points) < 2:
        return

    path = [tuple(p) for p in points]

    # Trim first and last points so connectors begin/end near node borders instead of centers.
    def shift_point(a, b, d):
        ax0, ay0 = a
        bx0, by0 = b
        dx = bx0 - ax0
        dy = by0 - ay0
        norm = (dx * dx + dy * dy) ** 0.5
        if norm == 0:
            return a
        return (ax0 + d * dx / norm, ay0 + d * dy / norm)

    trim = 0.8
    path[0] = shift_point(path[0], path[1], trim)
    path[-1] = shift_point(path[-1], path[-2], trim)

    for i in range(len(path) - 2):
        x1, y1 = path[i]
        x2, y2 = path[i + 1]
        ax.plot([x1, x2], [y1, y2], color="black", linewidth=lw, zorder=4)

    x1, y1 = path[-2]
    x2, y2 = path[-1]
    ax.annotate(
        "",
        xy=(x2, y2),
        xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle="-|>",
            lw=lw,
            color="black",
            mutation_scale=10,
            shrinkA=0,
            shrinkB=0,
        ),
        zorder=4,
    )


def add_label(ax, x, y, text):
    ax.text(x, y, text, ha="center", va="center", fontsize=8.5, zorder=6)


def add_connector_label(ax, points, text, segment_index=0, dx=0.0, dy=0.45):
    if segment_index < 0 or segment_index >= len(points) - 1:
        return
    x1, y1 = points[segment_index]
    x2, y2 = points[segment_index + 1]
    mx = (x1 + x2) / 2.0
    my = (y1 + y2) / 2.0
    add_label(ax, mx + dx, my + dy, text)


def build_flowchart(ax):
    nodes = {
        "start": (-1.5, 0),
        "end": (9.5, -5),
        "genes": (-1.5, -2),
        "gene": (-4, -9),
        "feature": (-1.5, -5),
        "trans": (-4, -13),
        "compound": (-4, -18),
        "adjacent": (-4, -23),
        "remove": (0, -11.5),
        "add_compound": (0, -9),
        "merge_cis": (0, -20),
        "merge_adj": (0, -24.5),
        "compound_feats": (5, -2),
        "simples": (14, -9),
        "simple": (7, -13),
        "has_compound": (9.5, -2),
        "has_simple": (9.5, -9),
        "can_insert": (7, -17.5),
        "can_merge": (7, -23),
        "sort": (14, -2),
        "make_simples": (14, -5),
        "insert": (11, -15.5),
        "merge_trans": (11, -21),
    }

    draw_terminator(ax, nodes["start"], "Start")
    draw_terminator(ax, nodes["end"], "End")

    draw_data(ax, nodes["genes"], "Gene features", color="#ffd6d6")
    draw_data(ax, nodes["gene"], "Gene feature", color="#ffd6d6")
    draw_data(ax, nodes["compound_feats"], "Compound features", color="#ffd6d6", width=4.8)
    draw_data(ax, nodes["simples"], "Simple features", color="#ffd6d6")
    draw_data(ax, nodes["simple"], "Gene feature", color="#ffd6d6")

    draw_decision(ax, nodes["feature"], "Unexamined\nfeature")
    draw_decision(ax, nodes["trans"], "Trans-spliced\ngene")
    draw_decision(ax, nodes["compound"], "Cis-spliced\ncompound\nlocation")
    draw_decision(ax, nodes["adjacent"], "Adjacent gene is\nthe same as\nfeature", height=2.6)
    draw_decision(ax, nodes["has_compound"], "Has\nfeatures")
    draw_decision(ax, nodes["has_simple"], "Unexamined\nfeature")
    draw_decision(ax, nodes["can_insert"], "Flanking genes not same\nas feature and\nno overlap", width=6.2, height=2.6)
    draw_decision(ax, nodes["can_merge"], "At least one flanking\ngene is the same\nas feature", width=6.2, height=2.6)

    draw_process(ax, nodes["remove"], "Remove from genes")
    draw_process(ax, nodes["add_compound"], "Add to compound\nfeatures")
    draw_process(ax, nodes["merge_cis"], "Merge locations")
    draw_process(ax, nodes["merge_adj"], "Merge genes")
    draw_process(ax, nodes["sort"], "Sort gene features")
    draw_process(ax, nodes["make_simples"], "Make simple features")
    draw_process(ax, nodes["insert"], "Insert gene")
    draw_process(ax, nodes["merge_trans"], "Merge into genes")

    # Connectors mirror the original TikZ paths.
    p_start_genes = [nodes["start"], nodes["genes"]]
    p_genes_feature = [nodes["genes"], nodes["feature"]]
    p_gene_trans = [nodes["gene"], nodes["trans"]]
    p_remove_add = [nodes["remove"], nodes["add_compound"]]
    p_add_out = [nodes["add_compound"], (3, -9)]
    p_mergecis_adjacent = [nodes["merge_cis"], nodes["adjacent"]]
    p_mergeadj_out = [nodes["merge_adj"], (3, -24.5)]

    p_feature_yes = [nodes["feature"], (-1.5, -7.5), (-4, -7.5), nodes["gene"]]
    p_trans_yes = [nodes["trans"], (-1.5, -13), nodes["remove"]]
    p_compound_yes = [nodes["compound"], (-1.5, -18), nodes["merge_cis"]]
    p_adjacent_yes = [nodes["adjacent"], (-1.5, -23), nodes["merge_adj"]]

    p_trans_no = [nodes["trans"], nodes["compound"]]
    p_compound_no = [nodes["compound"], nodes["adjacent"]]
    p_adjacent_no = [nodes["adjacent"], (3, -23), (3, -25.5), (3, -7.5), nodes["feature"]]

    p_compoundfeats_has = [nodes["compound_feats"], nodes["has_compound"]]
    p_sort_make = [nodes["sort"], nodes["make_simples"]]
    p_make_simples = [nodes["make_simples"], nodes["simples"]]
    p_simples_hassimple = [nodes["simples"], nodes["has_simple"]]
    p_simple_caninsert = [nodes["simple"], nodes["can_insert"]]
    p_insert_up = [nodes["insert"], (14, -15.5), (14, -14)]
    p_mergetrans_up = [nodes["merge_trans"], (14, -21), (14, -19)]

    p_hascompound_yes = [nodes["has_compound"], nodes["sort"]]
    p_hassimple_yes = [nodes["has_simple"], (9.5, -11.5), (7, -11.5), nodes["simple"]]
    p_caninsert_yes = [nodes["can_insert"], (11, -17.5), nodes["insert"]]
    p_canmerge_yes = [nodes["can_merge"], (11, -23), nodes["merge_trans"]]

    p_feature_no = [nodes["feature"], (5, -5), nodes["compound_feats"]]
    p_hassimple_no = [nodes["has_simple"], nodes["end"]]
    p_hascompound_no = [nodes["has_compound"], nodes["end"]]
    p_caninsert_no = [nodes["can_insert"], nodes["can_merge"]]
    p_canmerge_no = [nodes["can_merge"], (14, -23), (14, -25.5), (14, -11.5), nodes["has_simple"]]

    all_paths = [
        p_start_genes,
        p_genes_feature,
        p_gene_trans,
        p_remove_add,
        p_add_out,
        p_mergecis_adjacent,
        p_mergeadj_out,
        p_feature_yes,
        p_trans_yes,
        p_compound_yes,
        p_adjacent_yes,
        p_trans_no,
        p_compound_no,
        p_adjacent_no,
        p_compoundfeats_has,
        p_sort_make,
        p_make_simples,
        p_simples_hassimple,
        p_simple_caninsert,
        p_insert_up,
        p_mergetrans_up,
        p_hascompound_yes,
        p_hassimple_yes,
        p_caninsert_yes,
        p_canmerge_yes,
        p_feature_no,
        p_hassimple_no,
        p_hascompound_no,
        p_caninsert_no,
        p_canmerge_no,
    ]
    for p in all_paths:
        draw_connector(ax, p)

    # Path-anchored label placement, matching TikZ "midway, above, xshift" intent.
    add_connector_label(ax, p_feature_yes, "Yes", segment_index=1, dx=0.4, dy=0.4)
    add_connector_label(ax, p_trans_yes, "Yes", segment_index=0, dx=0.3, dy=0.4)
    add_connector_label(ax, p_compound_yes, "Yes", segment_index=0, dx=0.3, dy=0.4)
    add_connector_label(ax, p_adjacent_yes, "Yes", segment_index=0, dx=0.35, dy=0.4)

    add_connector_label(ax, p_trans_no, "No", segment_index=0, dx=0.0, dy=0.45)
    add_connector_label(ax, p_compound_no, "No", segment_index=0, dx=0.0, dy=0.45)
    add_connector_label(ax, p_adjacent_no, "No", segment_index=1, dx=0.0, dy=0.45)

    add_connector_label(ax, p_hascompound_yes, "Yes", segment_index=0, dx=0.0, dy=0.45)
    add_connector_label(ax, p_hassimple_yes, "Yes", segment_index=1, dx=0.3, dy=0.45)
    add_connector_label(ax, p_caninsert_yes, "Yes", segment_index=0, dx=0.2, dy=0.45)
    add_connector_label(ax, p_canmerge_yes, "Yes", segment_index=0, dx=0.2, dy=0.45)

    add_connector_label(ax, p_feature_no, "No", segment_index=0, dx=0.0, dy=0.45)
    add_connector_label(ax, p_hassimple_no, "No", segment_index=0, dx=0.4, dy=0.45)
    add_connector_label(ax, p_hascompound_no, "No", segment_index=0, dx=0.4, dy=0.45)
    add_connector_label(ax, p_caninsert_no, "No", segment_index=0, dx=0.0, dy=0.45)
    add_connector_label(ax, p_canmerge_no, "No", segment_index=1, dx=0.0, dy=0.45)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Render exon splicing flowchart from Python and export SVG/PNG."
    )
    parser.add_argument(
        "--output-dir",
        default="./VIZ_c_FlowchartExonSplicing",
        help="Directory to write output files.",
    )
    parser.add_argument(
        "--output-name",
        default="VIZ_FlowchartExonSplicing",
        help="Output file name with or without extension; script writes .svg and .png.",
    )
    return parser.parse_args()


def output_paths(output_dir, output_name):
    os.makedirs(output_dir, exist_ok=True)
    base = os.path.splitext(output_name)[0]
    return (
        os.path.join(output_dir, f"{base}.svg"),
        os.path.join(output_dir, f"{base}.png"),
    )


def main():
    args = parse_args()
    svg_path, png_path = output_paths(args.output_dir, args.output_name)

    fig, ax = plt.subplots(figsize=(14, 12))
    build_flowchart(ax)

    ax.set_xlim(-7, 18)
    ax.set_ylim(-27, 2)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()

    plt.savefig(svg_path, format="svg", dpi=300, bbox_inches="tight")
    plt.savefig(png_path, format="png", dpi=300, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()