import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Arc, Rectangle


# ---------------------------
# Helper functions
# ---------------------------
def polar_to_cart(r, theta_deg):
    theta = np.deg2rad(theta_deg)
    return r * np.cos(theta), r * np.sin(theta)


def draw_arc(ax, center, r, start, end, color, lw=4, alpha=0.95):
    cx, cy = center
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


def dotted_line(ax, x1, y1, x2, y2, dotsize=4, lw=1.0):
    # simple dotted line using many short segments for crispness at different dpi
    xs = np.linspace(x1, x2, 40)
    ys = np.linspace(y1, y2, 40)
    ax.plot(xs, ys, linestyle=":", color="black", linewidth=lw)


def draw_box(ax, x, y_center, w, h, color):
    rect = Rectangle((x, y_center - h / 2), w, h, fill=False, lw=2, edgecolor=color)
    ax.add_patch(rect)


# ---------------------------
# Layout parameters
# ---------------------------
fig, ax = plt.subplots(figsize=(14, 7))
ax.set_aspect("equal")
ax.axis("off")

# Circles (left)
R = 6.0
InnerR = 5.3
# Tight vertical stacking (top->middle->bottom)
y_top = 18.0  # choose positions so panel aligns nicely
spacing = -11.0
centers = [(0, y_top), (0, y_top + spacing), (0, y_top + 2 * spacing)]
labels = ["T3", "T2", "T1"]

# Colors
col_red = (228 / 255, 26 / 255, 28 / 255)
col_blue = (55 / 255, 126 / 255, 184 / 255)
col_green = (77 / 255, 175 / 255, 74 / 255)

# Gene arcs per genome (angles tuned visually)
genome_gene_angles = [
    [(150, 200, col_red), (310, 350, col_green), (230, 260, col_blue)],  # T3
    [(170, 210, col_red), (300, 330, col_green), (240, 270, col_blue)],  # T2
    [(180, 220, col_red), (290, 325, col_green), (250, 285, col_blue)],  # T1
]

# Draw left-hand circles + arcs
for center, label, genes in zip(centers, labels, genome_gene_angles):
    ax.add_patch(plt.Circle(center, R, fill=False, color="black", lw=2))
    for s, e, c in genes:
        draw_arc(ax, center, InnerR, s, e, color=c, lw=5)
    ax.text(center[0], center[1], label, ha="center", va="center", fontsize=14)

# ---------------------------
# Right-side linear panel (data-driven)
# ---------------------------
# panel origin
panel_x0 = 11.5
panel_top_y = y_top + 6.5  # header area

# Column layout (nominal positions used for guides — boxes are positioned explicitly)
col_gap = 6.8  # nominal column spacing (for header placement)

# Draw headers
headers = ["Gene 1", "Gene 2", "Gene 3", "Gene 4"]
for i, h in enumerate(headers):
    hx = panel_x0 + i * col_gap + 1.6
    hy = panel_top_y
    ax.text(hx, hy, h, ha="center", va="center", fontsize=14)

# Box geometry defaults
box_h = 1.0


T3_y = centers[0][1]
T3_row = [
    {"x": panel_x0 + 1.8, "w": 3.6, "color": col_green},  # Gene1 (small box)
    {"x": panel_x0 + col_gap + 1.8, "w": 3.6, "color": col_red},  # Gene2
    {
        "x": panel_x0 + 2 * col_gap + 1.8,
        "w": 3.6,
        "color": col_blue,
    },  # Gene3 (dotted before)
    {"x": panel_x0 + 3 * col_gap + 1.8, "w": 3.6, "color": col_red},  # Gene4
]

T2_y = centers[1][1]
T2_row = [
    {
        "x": panel_x0 + 0.8,
        "w": 6.8,
        "color": col_green,
    },  # Gene1 expanded (touches gene2)
    {
        "x": panel_x0 + 0.8 + 6.8,
        "w": 4.8,
        "color": col_red,
    },  # Gene2 starts immediately after gene1
    {
        "x": panel_x0 + 0.8 + 6.8 + 4.8,
        "w": 3.6,
        "color": col_blue,
    },  # Gene3 starts after gene2
    {
        "x": panel_x0 + 0.8 + 6.8 + 4.8 + 3.6 + 1.0,
        "w": 3.6,
        "color": col_red,
    },  # Gene4 (dotted before)
]

T1_y = centers[2][1]
T1_row = [
    {"x": panel_x0 + 1.8, "w": 3.6, "color": col_green},  # Gene1
    {
        "x": panel_x0 + col_gap + 1.1,
        "w": 3.6,
        "color": col_red,
    },  # Gene2 (dotted before)
    {"x": panel_x0 + 2 * col_gap + 1.8, "w": 3.6, "color": col_blue},  # Gene3
    {"x": panel_x0 + 3 * col_gap + 1.8, "w": 3.6, "color": col_red},  # Gene4
]

rows = [
    (T3_row, T3_y),
    (T2_row, T2_y),
    (T1_row, T1_y),
]

panel_left_guide_x = panel_x0 - 1.8

for row_idx, (row, y) in enumerate(rows):
    for gene_idx, entry in enumerate(row):
        if entry is None:
            continue
        x = entry["x"]
        w = entry["w"]
        color = entry["color"]

        if x - panel_left_guide_x > 1.2:
            dotted_line(ax, panel_left_guide_x, y, x - 0.4, y, lw=1.0)
        draw_box(ax, x, y, w, box_h, color)

bracket_x = panel_left_guide_x + 0.8
bracket_top = T3_y + 1.2
bracket_bottom = T1_y - 1.2
ax.plot([bracket_x, bracket_x], [bracket_bottom, bracket_top], color="black", lw=2)
ax.plot([bracket_x - 0.8, bracket_x], [bracket_top, bracket_top], color="black", lw=2)
ax.plot(
    [bracket_x - 0.8, bracket_x], [bracket_bottom, bracket_bottom], color="black", lw=2
)

# Clean margins and show
ax.set_xlim(-9, panel_x0 + 3 * col_gap + 10)
ax.set_ylim(T1_y - 12, T3_y + 12)
plt.tight_layout()
plt.show()
