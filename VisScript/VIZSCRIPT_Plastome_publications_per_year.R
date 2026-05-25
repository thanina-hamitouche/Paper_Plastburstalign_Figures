#!/usr/bin/R
# author: Michael Gruenstaeudl <m_gruenstaeudl@fhsu.edu>

library(argparse)
library(ggplot2)
library(plyr)  # For 'round_any()'
library(dplyr) # For '%>%'

################################################################################
### ARGPARSE BLOCK ###

parser <- ArgumentParser(
    description = "Generate a cumulative publications graph for plastid genomes."
)
parser$add_argument("--input", required = TRUE,
                    help = "Path to input CSV file with publication data (columns: publications, year).")
parser$add_argument("--output", default = "./Plastome_publications_per_year.svg",
                    help = "Output SVG filename (default: ./Plastome_publications_per_year.svg).")
args <- parser$parse_args()

################################################################################

outfilename <- args$output

if (!file.exists(args$input)) {
    stop(paste("Input file not found:", args$input), call. = FALSE)
}

inData <- read.csv(args$input, sep = ",", header = FALSE)
colnames(inData) <- c("publications", "year")

inData <- inData[order(inData$year, decreasing = FALSE), ]  # Sorting years oldest to newest
rownames(inData) <- seq(1, nrow(inData))  # Assigning new rownames (important for cumsum function)

plotData <- inData %>% mutate(CUMSUM = cumsum(inData$publications))
plotData <- plotData[order(plotData$year, decreasing = TRUE), ]  # Sorting years oldest on bottom

break_max <- round_any(max(plotData$CUMSUM), 100, f = ceiling)

################################################################################

base_plot <- ggplot(data = plotData, aes(x = year, y = CUMSUM)) +
    geom_bar(stat = "identity", position = "stack", alpha = 0.5)  # stacked barcharts

myPlot <- base_plot +
    xlab("Year") +
    ylab("Cumulative Number of Publications\n") +
    scale_x_continuous(
        breaks = plotData$year,
        labels = factor(plotData$year),
        minor_breaks = NULL,
        expand = expansion(0)
    ) +
    scale_y_continuous(breaks = seq(0, break_max, 100),
                       labels = function(x) format(x, big.mark = ",", scientific = FALSE, trim = TRUE),
                       minor_breaks = NULL) +
    theme_minimal() +
    theme(plot.title = element_text(size = 20),
          plot.subtitle = element_text(size = 20, face = "italic"),
          axis.text = element_text(size = 12),
          axis.text.x = element_text(size = 11, angle = 45, hjust = 0.5, vjust = 1.0),
          axis.ticks.x = element_line(color = "black"),
          axis.ticks.length = unit(0.2, "cm"),
          axis.title = element_text(size = 18, face = "bold"),
          plot.margin = unit(c(0.5, 1.0, 0.1, 0.1), "cm"),  # Order: t,r,b,l
          legend.key.width = unit(1, "cm"),
          legend.position = "bottom",
          legend.text = element_text(size = 14),
          legend.title = element_text(size = 14))

################################################################################

svg_device <- if (requireNamespace("svglite", quietly = TRUE)) {
    svglite::svglite
} else {
    grDevices::svg
}
ggsave(file = outfilename, plot = myPlot, width = 10, height = 5, device = svg_device)

################################################################################
