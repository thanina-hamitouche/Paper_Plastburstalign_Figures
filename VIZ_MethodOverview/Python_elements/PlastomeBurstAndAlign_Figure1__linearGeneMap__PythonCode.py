import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- Gene definitions (start, stop, color, label) ---
genes = [
    (10, 40, (228/255, 26/255, 28/255),  "Gene1"),
    (70, 110, (55/255, 126/255, 184/255), "Gene2"),
    (140, 180, (77/255, 175/255, 74/255), "Gene3"),
    (205, 230, (152/255, 78/255, 163/255), "Gene4"),
    (240, 265, (255/255, 127/255, 0/255), "Gene5"),
]

# --- Scale factor: bp to plotting units ---
SCALE = 0.05  # each bp = 0.05 cm equivalent

# --- Plot setup ---
fig, ax = plt.subplots(figsize=(8, 4))
ax.set_xlim(0, (genes[-1][1] + 20) * SCALE)
ax.set_ylim(-0.5, 2.0)
ax.axis('off')

# --- Drawing parameters ---
y_bottom = 0.3
height = 0.6

# --- Draw genes sequentially ---
x_prev = 0
for start, stop, color, label in genes:
    # Compute rectangle width (scaled)
    width = (stop - start) * SCALE

    # Draw rectangle
    rect = patches.Rectangle(
        (x_prev, y_bottom), width, height,
        linewidth=1.5, edgecolor=color,
        facecolor=(*color, 0.5)
    )
    ax.add_patch(rect)

    # Add label centered above gene
    mid_x = x_prev + width / 2
    ax.text(mid_x, y_bottom + height + 0.25, label,
            ha='center', va='bottom', fontsize=9)

    # Update running endpoint
    x_prev += width

# --- Draw genome axis ---
ax.plot([0, x_prev + 0.5], [-0.1, -0.1], color='black', lw=1.5)
ax.arrow(x_prev + 0.5, -0.1, 0.2, 0, head_width=0.08, head_length=0.15, fc='black', ec='black')

# --- Add genome label ---
ax.text(x_prev + 1.0, -0.25, "Genome 1 (linearized)", fontsize=10, va='top', ha='left')

plt.tight_layout()
plt.show()
