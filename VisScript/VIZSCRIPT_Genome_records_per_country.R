#!/usr/bin/R
# author: Michael Gruenstaeudl <m_gruenstaeudl@fhsu.edu>

library(argparse)
library(ggplot2)
library(dplyr) # For '%>%'

################################################################################
### ARGPARSE BLOCK ###

parser <- ArgumentParser(
    description = "Generate a genome-records-per-country bar chart."
)
parser$add_argument("--input", required = TRUE,
                    help = "Path to input CSV file (2 columns: records, country).")
parser$add_argument("--output", default = "./Genome_records_per_country.svg",
                    help = "Output SVG filename (default: ./Genome_records_per_country.svg).")
parser$add_argument("--min-records", type = "integer", default = 5,
                    help = "Minimum number of records to include a country (default: 5).")
args <- parser$parse_args()
outfilename <- args$output

################################################################################

if (!file.exists(args$input)) {
    stop(paste("Input file not found:", args$input), call. = FALSE)
}

if (args$min_records < 1) {
    stop("--min-records must be >= 1.", call. = FALSE)
}

## Load Plastome Availability Table (.csv-format)
inData = read.csv(args$input, sep = ",", header = FALSE, stringsAsFactors = FALSE)
colnames(inData) = c("records", "country")
# Get only countries with record number >= min-records
inData = inData[inData$records >= args$min_records, ]

if (nrow(inData) == 0) {
    stop("No countries remain after applying --min-records filter.", call. = FALSE)
}

################################################################################

myPlot = ggplot(data=inData, aes(x=reorder(country, records), y=records)) +
    geom_bar(stat="identity", position="identity", alpha=0.5) +
    ggtitle(paste0("Number of plastid genomes on NCBI Nucleotide per country (≥ ", args$min_records, ")")) +
    xlab("country of origin") +
    ylab("Number of genomes") +
    scale_y_continuous(labels=function(x) format(x, big.mark = ",", scientific = FALSE, trim = TRUE)) +
    theme_minimal() +
    theme(plot.title = element_text(size=20),
          axis.text.x=element_text(size=10, angle=45, hjust=1),
          axis.text.y=element_text(size=12),
          axis.title=element_text(size=16, face="bold"),
          plot.margin=unit(c(0.5,1.0,0.1,0.1),"cm")  # Note: margin(t=0, r=0, b=0, l=0, unit="pt")
    )

################################################################################

svg_device <- if (requireNamespace("svglite", quietly = TRUE)) {
    svglite::svglite
} else {
    grDevices::svg
}
ggsave(file=outfilename, plot=myPlot, width=15, height=10, device=svg_device)

################################################################################
