#!/usr/bin/R
# author: Michael Gruenstaeudl <m_gruenstaeudl@fhsu.edu>

library(argparse)
library(ggplot2)
library(plyr)  # For 'round_any()' 
library(dplyr) # For '%>%'

################################################################################
### ARGPARSE BLOCK ###

parser <- ArgumentParser(
    description = "Generate a family distribution graph of plastid genome records."
)
parser$add_argument("--input", required = TRUE,
                    help = "Path to input TSV file (output of script 1).")
parser$add_argument("--output", default = "./Family_distribution_graph.svg",
                    help = "Output SVG filename (default: ./Family_distribution_graph.svg).")
parser$add_argument("--taxonomy-column", default = "TAXONOMY",
                    help = "Column containing taxonomy strings (default: TAXONOMY).")
parser$add_argument("--top-n", type = "integer", default = 20,
                    help = "Number of top families to plot (default: 20).")
parser$add_argument("--family-pattern", default = "aceae",
                    help = "Pattern used to identify family names in taxonomy (default: aceae).")
args <- parser$parse_args()
outfilename <- args$output

################################################################################

if (!file.exists(args$input)) {
    stop(paste("Input file not found:", args$input), call. = FALSE)
}

if (args$top_n < 1) {
    stop("--top-n must be >= 1.", call. = FALSE)
}

AvailTableData <- read.csv(args$input, sep = "\t", stringsAsFactors = FALSE)

if (!(args$taxonomy_column %in% colnames(AvailTableData))) {
    stop(paste("Taxonomy column not found:", args$taxonomy_column), call. = FALSE)
}

AvailTableData$FAMILY = NA
for (i in 1:nrow(AvailTableData)){
    split = unlist(strsplit(AvailTableData[i,][[args$taxonomy_column]], ";"))
    family = split[grep(args$family_pattern, split)[1]]
    AvailTableData[i,]$FAMILY = family
}

AvailTableData <- AvailTableData[!is.na(AvailTableData$FAMILY), ]

if (nrow(AvailTableData) == 0) {
    stop("No family entries matched --family-pattern.", call. = FALSE)
}

plotData = as.data.frame(sort(table(AvailTableData$FAMILY), decreasing=TRUE))
colnames(plotData) = c("family", "cumsum")

max_rows <- min(args$top_n, nrow(plotData))

################################################################################

base_plot = ggplot(data=plotData[c(1:max_rows),], aes(x=family, y=cumsum)) + 
    geom_bar(stat="identity", position="stack", alpha=0.5) + # stacked barcharts
    geom_text(aes(label=cumsum), hjust=-0.20)

myPlot = base_plot + 
    ggtitle(paste0("Top-", args$top_n, " Plant Families by Number of Archived Plastid Genomes")) +
    xlab("") + 
    ylab("") + 
    theme_minimal() +
    scale_y_continuous(labels=function(x) format(x, big.mark = ",", scientific = FALSE, trim = TRUE)) +
    scale_x_discrete(limits=rev) + 
    coord_flip(clip = "off") + 
    theme(plot.title = element_text(size=20),
          plot.subtitle = element_text(size=20, face="italic"),
          axis.text=element_text(size=14),
          axis.text.x = element_text(size=12), #angle=45, hjust=0, vjust=0.5),
          #axis.title=element_text(size=18, face="bold"),
          plot.margin=unit(c(0.5,2.5,0.1,0.1),"cm"),  # Order: t,r,b,l
          legend.key.width=unit(1,"cm"),
          legend.position = "bottom",
          legend.text = element_text(size=14),
          legend.title = element_text(size=14))

################################################################################

svg_device <- if (requireNamespace("svglite", quietly = TRUE)) {
    svglite::svglite
} else {
    grDevices::svg
}
ggsave(file=outfilename, plot=myPlot, width=10, height=5, device=svg_device)

################################################################################
