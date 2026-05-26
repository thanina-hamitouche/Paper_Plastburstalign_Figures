import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Arc

# --- Setup ---
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_aspect('equal')
ax.axis('off')

# --- Parameters (cm → convert to arbitrary units) ---
MainR = 6.0        # outer genome radius
InnerR = 5.5       # gene arc radius
TickHalf = 0.10
TickHalfZero = 0.175
LabelOffset = 0.45

# --- Colors ---
colors = {
    'gene1': (228/255, 26/255, 28/255),
    'gene2': (55/255, 126/255, 184/255),
    'gene3': (77/255, 175/255, 74/255),
    'gene4': (152/255, 78/255, 163/255),
    'gene5': (255/255, 127/255, 0/255),
}

# --- Helper functions ---
def polar_to_cart(r, theta_deg):
    theta = np.deg2rad(theta_deg)
    return r * np.cos(theta), r * np.sin(theta)

def draw_arc(ax, r, start, end, color='k', lw=2, alpha=1.0):
    # Matplotlib Arc uses center/width/height, angles in degrees
    arc = Arc((0, 0), width=2*r, height=2*r, theta1=start, theta2=end,
              color=color, lw=lw, alpha=alpha, capstyle='butt')
    ax.add_patch(arc)

# --- Genome ring ---
circle = plt.Circle((0, 0), MainR, fill=False, lw=2, color='black')
ax.add_patch(circle)

# --- Tick marks and labels ---
# Origin tick (0°)
x1, y1 = polar_to_cart(MainR - TickHalfZero, 0)
x2, y2 = polar_to_cart(MainR + TickHalfZero, 0)
ax.plot([x1, x2], [y1, y2], color='black', lw=1.5)
xlab, ylab = polar_to_cart(MainR + LabelOffset, 0)
ax.text(xlab, ylab, "0", ha='center', va='center', fontsize=8)

# Regular ticks every 10 k (approx 23° apart)
tick_angles_labels = [
    (23, "10k"), (45, "20k"), (68, "30k"), (90, "40k"),
    (113, "50k"), (135, "60k"), (158, "70k"), (180, "80k"),
    (203, "90k"), (225, "100k"), (248, "110k"), (270, "120k"),
    (293, "130k"), (315, "140k"), (338, "150k")
]

for ang, lab in tick_angles_labels:
    x1, y1 = polar_to_cart(MainR - TickHalf, ang)
    x2, y2 = polar_to_cart(MainR + TickHalf, ang)
    ax.plot([x1, x2], [y1, y2], color='black', lw=0.5)
    xlab, ylab = polar_to_cart(MainR + LabelOffset, ang)
    ax.text(xlab, ylab, lab, ha='center', va='center', fontsize=8)

# --- IR definitions ---
IRbStart, IRbEnd = 200, 270
IRaStart, IRaEnd = 292.5, 360
IRbLen = IRbEnd - IRbStart
IRaLen = IRaEnd - IRaStart
IRscale = IRaLen / IRbLen

# --- Draw IR regions ---
draw_arc(ax, MainR, IRbStart, IRbEnd, color='gray', lw=10, alpha=0.5)
mid_ang = (IRbStart + IRbEnd) / 2
xlab, ylab = polar_to_cart(MainR + 0.7, mid_ang)
ax.text(xlab, ylab, "IRb", fontsize=12, ha='center', va='center')

draw_arc(ax, MainR, IRaStart, IRaEnd, color='gray', lw=10, alpha=0.5)
mid_ang = (IRaStart + IRaEnd) / 2
xlab, ylab = polar_to_cart(MainR + 0.7, mid_ang)
ax.text(xlab, ylab, "IRa", fontsize=12, ha='center', va='center')

# --- Genes outside IR regions ---
GeneList = [
    (10, 40, 'gene1'),
    (70, 110, 'gene2'),
    (140, 180, 'gene3'),
]

for start, stop, col in GeneList:
    draw_arc(ax, InnerR, start, stop, color=colors[col], lw=4, alpha=0.85)

# --- Genes inside IRb ---
IRGeneList = [
    (205, 230, 'gene4'),
    (240, 265, 'gene5'),
]
for start, stop, col in IRGeneList:
    draw_arc(ax, InnerR, start, stop, color=colors[col], lw=4, alpha=0.85)

# --- Reverse complement genes in IRa ---
for s, t, col in IRGeneList:
    s_prime = IRaEnd - (t - IRbStart) * IRscale
    t_prime = IRaEnd - (s - IRbStart) * IRscale
    draw_arc(ax, InnerR, s_prime, t_prime, color=colors[col], lw=4, alpha=0.85)

# --- Center label ---
ax.text(0, 0, "Genome 1", ha='center', va='center', fontsize=14)

plt.tight_layout()
plt.show()
