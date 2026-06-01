library(plyr)
library(ggplot2)
library(svglite)

inFn = "./results/plastburst_benchmark_Final.csv"
ouDr = dirname(inFn)
plotData = read.csv(inFn, header = TRUE)

# Ensure factors
plotData$MARKER  = factor(plotData$MARKER, levels = c("cds", "igs", "int"))
plotData$DATASET = factor(plotData$DATASET)

max_time = round_any(max(plotData$TIME), 10, f = ceiling)

myPlot = ggplot(
  plotData,
  aes(
    x = CPUS,
    y = TIME,
    color = DATASET,
    group = DATASET
  )
) +
  geom_point(size = 3) +
  geom_line() +
  geom_text(
    aes(label = paste(round(TIME, 2), "sec")),
    size = 3,
    vjust = -0.35,
    hjust = -0.15,
    show.legend = FALSE
  ) +
  scale_x_continuous(
    breaks = c(1,2,4,8,16),
    limits = c(1,16)
  ) +
  scale_y_log10(
    limits = c(5, max_time)
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
    "Monocot(n=733)",
    "Angiosperms (n=2585)"
  )
) +
  facet_wrap(~ MARKER, ncol = 1, scales = "fixed") +
  xlab("\nNumber of CPUs") +
  ylab("Computation Time (seconds) – log-scale\n") +
#   ggtitle("Speed improvements through MPI implementation\n") +
  theme_minimal() +
  theme(
    plot.title = element_text(size = 18, hjust = 0.5),
    strip.text = element_text(size = 14, face = "bold"),
    axis.text = element_text(size = 12, color = "gray"),
    axis.title = element_text(size = 14),
    legend.position = "top",
    legend.key.width = unit(1, "cm"),
    panel.grid.major = element_line(color = "gray"),
    panel.grid.minor = element_line(color = "gray")
  )

out_fn = paste0(ouDr, "/PlastomeBurst_SpeedImprovements_AllMarkers.svg")
svglite(out_fn, width =13, height = 16)
print(myPlot)
dev.off()
