library(plyr)
library(ggplot2)
library(svglite)
library(ggrepel)

args = commandArgs(trailingOnly = TRUE)
if (length(args) < 2) {
  stop(
    "Usage: Rscript CODE_d_SpeedImprovements.R <input_csv> <output_path_stem>",
    call. = FALSE
  )
}

inFn = args[1]
outPathStem = args[2]
ouDr = dirname(outPathStem)

if (!file.exists(inFn)) {
  stop(paste("Input file does not exist:", inFn), call. = FALSE)
}

if (!dir.exists(ouDr)) {
  dir.create(ouDr, recursive = TRUE, showWarnings = FALSE)
}

plotData = read.csv(inFn, header = TRUE)

# Ensure factors
plotData$MARKER  = toupper(as.character(plotData$MARKER))
plotData$MARKER  = factor(plotData$MARKER, levels = c("CDS", "IGS", "INT"))
plotData$DATASET = factor(plotData$DATASET)
plotData$TIME_MIN = plotData$TIME / 60
max_cpus = max(plotData$CPUS, na.rm = TRUE)
x_breaks = unique(2^(0:ceiling(log(max_cpus, base = 2))))
x_breaks = x_breaks[x_breaks <= max_cpus]
if (!(max_cpus %in% x_breaks)) {
  x_breaks = sort(unique(c(x_breaks, max_cpus)))
}

max_time = round_any(max(plotData$TIME_MIN, na.rm = TRUE), 1, f = ceiling)
y_breaks_base = c(0, 1, 5, 10, 20, 40, 60, 120, 240)
if (max_time > max(y_breaks_base)) {
  y_breaks_extra = 240 * (2^(1:ceiling(log(max_time / 240, base = 2))))
  y_breaks = sort(unique(c(y_breaks_base, y_breaks_extra)))
} else {
  y_breaks = y_breaks_base
}
y_breaks = y_breaks[y_breaks <= max_time]

format_duration_labels = function(x_min) {
  format_min_value = function(x) {
    out = format(round(x, 1), nsmall = 1, trim = TRUE)
    sub("\\.0$", "", out)
  }

  out = character(length(x_min))

  is_na = is.na(x_min)
  out[is_na] = NA_character_

  idx_sec = !is_na & x_min < 1
  out[idx_sec] = paste0(round(x_min[idx_sec] * 60), " sec")

  idx_hr = !is_na & x_min > 60
  if (any(idx_hr)) {
    total_minutes = x_min[idx_hr]
    total_minutes = round(total_minutes)
    hrs = floor(total_minutes / 60)
    mins = total_minutes - (hrs * 60)
    roll_idx = mins >= 60
    if (any(roll_idx)) {
      hrs[roll_idx] = hrs[roll_idx] + 1
      mins[roll_idx] = 0
    }
    out[idx_hr] = ifelse(mins == 0,
      paste0(hrs, " h"),
      paste0(hrs, " h ", mins, " min")
    )
  }

  idx_min = !is_na & !idx_sec & !idx_hr
  out[idx_min] = paste0(format_min_value(x_min[idx_min]), " min")

  out
}

myPlot = ggplot(
  plotData,
  aes(
    x = CPUS,
    y = TIME_MIN,
    color = DATASET,
    linetype = MARKER,
    group = interaction(DATASET, MARKER)
  )
) +
  geom_vline(xintercept = 1, color = "black", linewidth = 0.4) +
  geom_hline(yintercept = 0, color = "black", linewidth = 0.4) +
  geom_point(size = 3) +
  geom_line(linewidth = 0.75) +
  geom_label_repel(
    aes(label = format_duration_labels(TIME_MIN)),
    family = "Arial",
    size = 3.6,
    box.padding = 0.2,
    point.padding = 0.15,
    label.padding = unit(0.08, "lines"),
    label.size = 0,
    fill = scales::alpha("white", 0.5),
    segment.color = "gray60",
    segment.size = 0.25,
    show.legend = FALSE
  ) +
  scale_x_continuous(
    trans = scales::pseudo_log_trans(base = 2),
    breaks = x_breaks,
    minor_breaks = NULL,
    limits = c(1, max(x_breaks)),
    expand = expansion(mult = c(0, 0.05))
  ) +
  scale_y_continuous(
    trans = scales::pseudo_log_trans(base = 10),
    breaks = y_breaks,
    labels = format_duration_labels,
    minor_breaks = NULL,
    limits = c(0, max_time),
    expand = expansion(mult = c(0, 0.02))
  ) +
  scale_color_manual(
  values = c(
    "benchmark_YangEtAl2022_Asteraceae"  = "darkgreen",
    "benchmark_YangEtAl2022_monocots"    = "blue",
    "benchmark_YangEtAl2022_angiosperms" = "maroon"
  ),
  breaks = c(
    "benchmark_YangEtAl2022_Asteraceae",
    "benchmark_YangEtAl2022_monocots",
    "benchmark_YangEtAl2022_angiosperms"
  ),
  labels = c(
    "Asteraceae (n=155)",
    "Monocot (n=733)",
    "Angiosperms (n=2,585)"
  )
) +
  scale_linetype_manual(
    values = c(
      "CDS" = "solid",
      "IGS" = "dotted",
      "INT" = "dashed"
    ),
    breaks = c("CDS", "INT", "IGS")
  ) +
  guides(
    color = guide_legend(order = 1),
    linetype = guide_legend(order = 2)
  ) +
  coord_cartesian(clip = "off") +
  xlab("\nNumber of CPUs\n(log2 scale)") +
  ylab("Computation Time\n(log10 scale)\n") +
  ggtitle("Speed improvements through MPI implementation\n") +
  theme_minimal(base_family = "Arial") +
  theme(
    text = element_text(family = "Arial"),
    plot.title = element_text(size = 18, hjust = 0.5, margin = margin(b = 4)),
    strip.text = element_text(size = 14, face = "bold"),
    axis.text = element_text(size = 14, color = "gray30"),
    axis.title = element_text(size = 14),
    legend.position = "top",
    legend.box = "vertical",
    legend.spacing.y = unit(0.1, "cm"),
    legend.margin = margin(t = 0, r = 0, b = 0, l = 0),
    legend.box.margin = margin(t = 0, r = 0, b = 0, l = 0),
    legend.title = element_text(size = 14),
    legend.text = element_text(size = 13),
    legend.key.width = unit(1.4, "cm"),
    legend.key.height = unit(0.8, "cm"),
    panel.grid.major = element_line(color = "gray"),
    panel.grid.minor = element_line(color = "gray"),
    panel.grid.minor.x = element_blank(),
    panel.grid.minor.y = element_blank(),
    plot.margin = margin(5.5, 28, 5.5, 5.5)
  )

out_fn_svg = paste0(outPathStem, ".svg")
out_fn_png = paste0(outPathStem, ".png")

svglite(out_fn_svg, width = 13, height = 16)
print(myPlot)
dev.off()

ggsave(out_fn_png, plot = myPlot, width = 13, height = 16, dpi = 300)
