#!/usr/bin/R
# author: Michael Gruenstaeudl <m_gruenstaeudl@fhsu.edu>

library(argparse)
library(ggplot2)
library(plyr)  # For 'round_any()' 
library(dplyr) # For '%>%'

################################################################################
### ARGPARSE BLOCK ###

parser <- ArgumentParser(
    description = "Generate an accumulation graph of plastid genome records."
)
parser$add_argument("--input", required = TRUE,
                    help = "Path to input TSV file (output of script 1).")
parser$add_argument("--start-date", default = "2000-01-01",
                    help = "Start date in YYYY-MM-DD format (default: 2000-01-01).")
parser$add_argument("--end-date", default = "2025-02-06",
                    help = "End date in YYYY-MM-DD format (default: 2025-02-06).")
parser$add_argument("--output", default = "./Accumulation_graph_plastid_genomes.svg",
                    help = "Output filename or basename; script writes both .svg and .png (default basename: ./Accumulation_graph_plastid_genomes).")
parser$add_argument("--date-column", default = "CREATE_DATE",
                    help = "Column name containing dates (default: CREATE_DATE).")
args <- parser$parse_args()

################################################################################

start_date <- as.Date(args$start_date, format = "%Y-%m-%d")
end_date <- as.Date(args$end_date, format = "%Y-%m-%d")
outfilename <- args$output
output_base <- tools::file_path_sans_ext(outfilename)
svg_outfile <- paste0(output_base, ".svg")
png_outfile <- paste0(output_base, ".png")

if (is.na(start_date) || is.na(end_date)) {
    stop("--start-date and --end-date must be in YYYY-MM-DD format.", call. = FALSE)
}

if (end_date < start_date) {
    stop("--end-date must be greater than or equal to --start-date.", call. = FALSE)
}

if (!file.exists(args$input)) {
    stop(paste("Input file not found:", args$input), call. = FALSE)
}

AvailTableData <- read.csv(args$input, sep = "\t", stringsAsFactors = FALSE)

if (!(args$date_column %in% colnames(AvailTableData))) {
    stop(paste("Date column not found:", args$date_column), call. = FALSE)
}

datesData = as.Date(AvailTableData[[args$date_column]], format="%Y-%m-%d")
datesData = datesData[!is.na(datesData)]

if (length(datesData) == 0) {
    stop("No valid dates found in input after parsing.", call. = FALSE)
}

monthlyData = table(cut(datesData, 'month'))
plotData = data.frame(DATE=as.Date(names(monthlyData)), FREQ_RECORDS=as.vector(monthlyData))
plotData = plotData[order(plotData$DATE),]
plotData = plotData %>% mutate(CUMFREQ=cumsum(FREQ_RECORDS))

break_max = round_any(max(plotData$CUMFREQ), 5000, f=ceiling)

################################################################################

base_plot = ggplot(data=plotData, aes(x=DATE, y=CUMFREQ)) + 
    geom_bar(stat="identity", position="stack", alpha=0.5) # stacked barcharts

myPlot = base_plot + 
    xlab("Year") + 
    ylab("Cumulative Number of Records\n") + 
    scale_x_date(
        date_breaks="1 year",
        minor_breaks=NULL,
        expand=expansion(0),
        date_labels="%Y"
    ) + 
    coord_cartesian(xlim = c(start_date, end_date), expand = FALSE) +
    scale_y_continuous(breaks=seq(0, break_max, 5000),
                       labels=function(x) format(x, big.mark = ",", scientific = FALSE, trim = TRUE),
                       minor_breaks=NULL) +
        theme_minimal(base_family = "Arial") + 
    theme(plot.title = element_text(size=20),
          plot.subtitle = element_text(size=20, face="italic"),
            text = element_text(family = "Arial"),
                        axis.text=element_text(size=12),
                        axis.text.x = element_text(size=11, angle=90, hjust=0.5, vjust=2.0),
                    axis.ticks.x = element_line(color="black"),
                    axis.ticks.length = unit(0.2, "cm"),
          axis.title=element_text(size=18, face="bold"),
          plot.margin=unit(c(0.5,1.0,0.1,0.1),"cm"),  # Order: t,r,b,l
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
ggsave(file=svg_outfile, plot=myPlot, width=10, height=5, device=svg_device)
ggsave(file=png_outfile, plot=myPlot, width=10, height=5, dpi=300)

################################################################################
