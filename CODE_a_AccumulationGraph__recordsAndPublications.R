#!/usr/bin/R
# author: Michael Gruenstaeudl <m_gruenstaeudl@fhsu.edu>

library(argparse)
library(ggplot2)
library(dplyr)

################################################################################
### ARGPARSE BLOCK ###

parser <- ArgumentParser(
    description = "Generate a combined accumulation graph of plastid genome records (bars) and publications (line)."
)

parser$add_argument("--input-records", required = TRUE)
parser$add_argument("--input-publications", required = TRUE)
parser$add_argument("--start-date", default = "2000-01-01")
parser$add_argument("--end-date", default = "2026-12-31")
parser$add_argument("--date-column", default = "CREATE_DATE")
parser$add_argument(
    "--output",
    default = "./VIZ_a_AccumulationGraphs/AccumulationGraph__recordsAndPublications"
)

args <- parser$parse_args()

################################################################################
### Fixed plotting range ###

plot_start_year <- 2000
plot_end_year <- 2026

plot_start_date <- as.Date(paste0(plot_start_year, "-01-01"))
plot_end_date <- as.Date(paste0(plot_end_year, "-12-31"))

if (!file.exists(args$input_records)) {
    stop(paste("Genome records input file not found:", args$input_records), call. = FALSE)
}

if (!file.exists(args$input_publications)) {
    stop(paste("Publications input file not found:", args$input_publications), call. = FALSE)
}

output_base <- tools::file_path_sans_ext(args$output)
svg_outfile <- paste0(output_base, ".svg")
png_outfile <- paste0(output_base, ".png")

dir.create(dirname(svg_outfile), recursive = TRUE, showWarnings = FALSE)

################################################################################
### Read and process genome records ###

records_data <- read.csv(args$input_records, sep = "\t", stringsAsFactors = FALSE)

if (!(args$date_column %in% colnames(records_data))) {
    stop(paste("Date column not found in genome records input:", args$date_column), call. = FALSE)
}

record_dates <- as.Date(records_data[[args$date_column]], format = "%Y-%m-%d")
record_dates <- record_dates[!is.na(record_dates)]
record_dates <- record_dates[record_dates >= plot_start_date & record_dates <= plot_end_date]

if (length(record_dates) == 0) {
    stop("No valid genome record dates found in the selected date range.", call. = FALSE)
}

month_seq <- seq(
    from = as.Date(paste0(plot_start_year, "-01-01")),
    to = as.Date(paste0(plot_end_year, "-12-01")),
    by = "month"
)

monthly_counts <- table(cut(record_dates, "month"))

plot_records <- data.frame(DATE = month_seq, stringsAsFactors = FALSE)
plot_records$FREQ_RECORDS <- as.integer(monthly_counts[as.character(plot_records$DATE)])
plot_records$FREQ_RECORDS[is.na(plot_records$FREQ_RECORDS)] <- 0
plot_records$CUM_RECORDS <- cumsum(plot_records$FREQ_RECORDS)

################################################################################
### Read and process publications ###

pub_data <- read.csv(
    args$input_publications,
    sep = ",",
    header = FALSE,
    stringsAsFactors = FALSE
)

if (ncol(pub_data) < 2) {
    stop("Publications input must contain at least two columns: publications, year.", call. = FALSE)
}

pub_data <- pub_data[, 1:2]
colnames(pub_data) <- c("publications", "year")

pub_data$year <- as.integer(pub_data$year)
pub_data$publications <- as.numeric(pub_data$publications)

pub_data <- pub_data[!is.na(pub_data$year) & !is.na(pub_data$publications), ]
pub_data <- pub_data[pub_data$year >= plot_start_year & pub_data$year <= plot_end_year, ]

if (nrow(pub_data) == 0) {
    stop("No valid publication data found in the selected year range.", call. = FALSE)
}

pub_data <- pub_data %>%
    group_by(year) %>%
    summarize(publications = sum(publications), .groups = "drop")

plot_publications <- data.frame(year = seq(plot_start_year, plot_end_year, by = 1))

plot_publications <- merge(plot_publications, pub_data, by = "year", all.x = TRUE)
plot_publications$publications[is.na(plot_publications$publications)] <- 0
plot_publications <- plot_publications[order(plot_publications$year), ]

plot_publications$CUM_PUBLICATIONS <- cumsum(plot_publications$publications)
plot_publications$DATE <- as.Date(paste0(plot_publications$year, "-01-01"))

################################################################################
### Axis scaling ###

max_records <- max(plot_records$CUM_RECORDS, na.rm = TRUE)
max_publications <- max(plot_publications$CUM_PUBLICATIONS, na.rm = TRUE)

if (max_records <= 0) {
    stop("Genome records cumulative total is zero; unable to plot.", call. = FALSE)
}

if (max_publications <= 0) {
    stop("Publication cumulative total is zero; unable to plot secondary axis.", call. = FALSE)
}

records_ylim <- ceiling(max_records / 5000) * 5000
records_ylim <- records_ylim + 5000

publications_ylim <- ceiling(max_publications * 1.20)

records_breaks <- seq(0, records_ylim, by = 5000)

scale_factor <- records_ylim / publications_ylim

plot_publications$CUM_PUBLICATIONS_SCALED <-
    plot_publications$CUM_PUBLICATIONS * scale_factor

publication_breaks <- pretty(c(0, publications_ylim), n = 8)
publication_breaks <- publication_breaks[
    publication_breaks >= 0 &
    publication_breaks <= publications_ylim
]

publication_breaks_scaled <- publication_breaks * scale_factor

################################################################################
### Calculate average yearly growth for the last five years ###

growth_years <- (plot_end_year - 4):plot_end_year

records_by_year <- plot_records %>%
    mutate(year = as.integer(format(DATE, "%Y"))) %>%
    group_by(year) %>%
    summarize(yearly_records = sum(FREQ_RECORDS), .groups = "drop")

avg_records_growth <- records_by_year %>%
    filter(year %in% growth_years) %>%
    summarize(avg = mean(yearly_records, na.rm = TRUE)) %>%
    pull(avg)

avg_publications_growth <- plot_publications %>%
    filter(year %in% growth_years) %>%
    summarize(avg = mean(publications, na.rm = TRUE)) %>%
    pull(avg)

label_records <- if (length(avg_records_growth) == 1 && !is.na(avg_records_growth)) {
    paste0(
        "Estimated yearly growth of records: ",
        format(round(avg_records_growth, 1), big.mark = ",")
    )
} else {
    "Estimated yearly growth of records: n/a"
}

label_publications <- if (length(avg_publications_growth) == 1 && !is.na(avg_publications_growth)) {
    paste0(
        "Estimated yearly growth of publications: ",
        format(round(avg_publications_growth, 1), big.mark = ",")
    )
} else {
    "Estimated yearly growth of publications: n/a"
}

annotation_text <- paste0(label_records, "\n", label_publications)

################################################################################
### Plot ###

myPlot <- ggplot() +

    geom_hline(
        yintercept = publication_breaks_scaled[publication_breaks > 0],
        color = "#1f77b4",
        linetype = "dashed",
        linewidth = 0.3,
        alpha = 0.45
    ) +

    geom_col(
        data = plot_records,
        aes(x = DATE, y = CUM_RECORDS),
        fill = "grey55",
        alpha = 0.55,
        width = 25
    ) +

    geom_line(
        data = plot_publications,
        aes(x = DATE, y = CUM_PUBLICATIONS_SCALED),
        color = "#1f77b4",
        linewidth = 1.3
    ) +

    geom_point(
        data = plot_publications,
        aes(x = DATE, y = CUM_PUBLICATIONS_SCALED),
        color = "#1f77b4",
        size = 2.0
    ) +

    labs(
        x = "Year",
        title = annotation_text
    ) +

    scale_x_date(
        breaks = as.Date(paste0(seq(plot_start_year, plot_end_year, by = 1), "-01-01")),
        date_labels = "%Y",
        minor_breaks = NULL,
        expand = expansion(mult = c(0.01, 0.01))
    ) +

    scale_y_continuous(
        name = "Cumulative Number of Records",
        limits = c(0, records_ylim),
        breaks = records_breaks,
        labels = function(x) format(x, big.mark = ",", scientific = FALSE, trim = TRUE),
        minor_breaks = NULL,
        expand = expansion(mult = c(0, 0.02)),
        sec.axis = sec_axis(
            transform = ~ . / scale_factor,
            name = "Cumulative Number of Publications",
            breaks = publication_breaks,
            labels = function(x) format(as.integer(round(x)), big.mark = ",", scientific = FALSE, trim = TRUE)
        )
    ) +

    coord_cartesian(
        xlim = c(plot_start_date, plot_end_date),
        clip = "off"
    ) +

    theme_minimal(base_family = "Arial") +

    theme(
        text = element_text(family = "Arial"),
        plot.title = element_text(
            size = 14,
            face = "bold",
            hjust = 0.5,
            margin = margin(b = 12)
        ),
        axis.text = element_text(size = 12),
        axis.text.x = element_text(size = 11, angle = 90, hjust = 0.5, vjust = 2.0),
        axis.ticks.x = element_line(color = "black"),
        axis.ticks.length = unit(0.2, "cm"),
        axis.title.x = element_text(size = 16, face = "bold"),
        axis.title.y.left = element_text(size = 15, face = "bold"),
        axis.title.y.right = element_text(size = 15, face = "bold", color = "#1f77b4"),
        axis.text.y.right = element_text(color = "#1f77b4"),
        plot.margin = unit(c(0.4, 1.2, 0.1, 0.1), "cm")
    )

################################################################################
### Save plot ###

svg_device <- if (requireNamespace("svglite", quietly = TRUE)) {
    svglite::svglite
} else {
    grDevices::svg
}

ggsave(file = svg_outfile, plot = myPlot, width = 10, height = 6.5, device = svg_device)
ggsave(file = png_outfile, plot = myPlot, width = 10, height = 6.5, dpi = 300)

################################################################################