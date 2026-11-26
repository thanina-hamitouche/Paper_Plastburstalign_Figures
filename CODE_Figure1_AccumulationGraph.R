
# Combined Accumulation Graph: Genome Records (bars) & Publications (line)
# Author: Michael Gruenstaeudl <m_gruenstaeudl@fhsu.edu>

ensure_dependencies <- function() {
    packages <- c("argparse", "ggplot2", "ggrepel", "ggtext", "plyr", "dplyr", "svglite", "jsonlite", "systemfonts")
    missing <- packages[!vapply(packages, requireNamespace, logical(1), quietly = TRUE)]
    if (length(missing) > 0) {
        install.packages(missing, repos = "https://cloud.r-project.org")
        missing <- packages[!vapply(packages, requireNamespace, logical(1), quietly = TRUE)]
        if (length(missing) > 0) {
            stop(paste("Failed to install R packages:", paste(missing, collapse = ", ")), call. = FALSE)
        }
    }
}

ensure_dependencies()

script_argument <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
script_dir <- if (length(script_argument) > 0) {
    dirname(normalizePath(sub("^--file=", "", script_argument[[1]])))
} else {
    getwd()
}
typography <- jsonlite::fromJSON(file.path(script_dir, "figure_typography.json"))
available_fonts <- unique(systemfonts::system_fonts()$family)
font_candidates <- c(typography$font_family, typography$fallback_families)
font_index <- match(tolower(font_candidates), tolower(available_fonts))
available_index <- which(!is.na(font_index))
if (length(available_index) == 0) {
    stop(paste("No supported figure font found:", paste(font_candidates, collapse = ", ")), call. = FALSE)
}
figure_font <- available_fonts[font_index[available_index[[1]]]]

relative_output_directory <- function(directory) {
    target <- normalizePath(directory, winslash = "/", mustWork = TRUE)
    current <- normalizePath(getwd(), winslash = "/", mustWork = TRUE)
    target_parts <- strsplit(target, "/", fixed = TRUE)[[1]]
    current_parts <- strsplit(current, "/", fixed = TRUE)[[1]]
    target_compare <- target_parts
    current_compare <- current_parts
    if (.Platform$OS.type == "windows") {
        target_compare <- tolower(target_compare)
        current_compare <- tolower(current_compare)
    }
    common <- 0L
    while (common < min(length(target_parts), length(current_parts)) &&
           identical(target_compare[common + 1L], current_compare[common + 1L])) {
        common <- common + 1L
    }
    if (.Platform$OS.type == "windows" &&
        (common == 0L || (startsWith(target, "//") && common < 4L))) {
        return(paste0(target, " (absolute path; relative path unavailable)"))
    }
    remaining <- if (common < length(target_parts)) {
        target_parts[seq.int(common + 1L, length(target_parts))]
    } else {
        character(0)
    }
    parts <- c(rep("..", length(current_parts) - common), remaining)
    if (length(parts) == 0) "." else paste(parts, collapse = "/")
}

suppressPackageStartupMessages({
  library(ggplot2)
  library(dplyr)
})
library(argparse)
library(ggtext)  # For colored annotation in plot title


# --- Argument Parsing ---
parser <- ArgumentParser(description = "Generate a combined accumulation graph of plastid genome records (bars) and publications (line).")
parser$add_argument("--input-records", required = TRUE)
parser$add_argument("--input-csv", "--input-publications", dest = "input_csv", required = TRUE)
parser$add_argument("--start-date", default = "2016-01-01")
parser$add_argument("--end-date", default = "2025-12-31")
parser$add_argument("--date-column", default = "CREATE_DATE")
parser$add_argument("--output-prefix", "--output", dest = "output_prefix", default = "./VIZ_Figure1_AccumulationGraph/Figure1_AccumulationGraph__recordsAndPublications")
args <- parser$parse_args()


# --- Plotting Range ---
plot_start_date <- as.Date(args$start_date)
plot_end_date <- as.Date(args$end_date)

if (is.na(plot_start_date) || is.na(plot_end_date)) {
    stop("Start date and end date must be valid YYYY-MM-DD values.", call. = FALSE)
}

if (plot_start_date > plot_end_date) {
    stop("Start date must be on or before end date.", call. = FALSE)
}

plot_start_year <- as.integer(format(plot_start_date, "%Y"))
plot_end_year <- as.integer(format(plot_end_date, "%Y"))
plot_start_month <- as.Date(format(plot_start_date, "%Y-%m-01"))
plot_end_month <- as.Date(format(plot_end_date, "%Y-%m-01"))
accumulation_start_year <- 2000
accumulation_start_date <- as.Date(paste0(accumulation_start_year, "-01-01"))


output_base <- paste0(tools::file_path_sans_ext(args$output_prefix), format(Sys.Date(), "__%Y_%m_%d"))
svg_outfile <- paste0(output_base, ".svg")
png_outfile <- paste0(output_base, ".png")
pdf_outfile <- paste0(output_base, ".pdf")

if (!file.exists(args$input_records)) {
    stop(paste("Genome records input file not found:", args$input_records), call. = FALSE)
}

if (!file.exists(args$input_csv)) {
    stop(paste("Publications input file not found:", args$input_csv), call. = FALSE)
}

dir.create(dirname(svg_outfile), recursive = TRUE, showWarnings = FALSE)


# --- Read and Process Genome Records ---
records_data <- read.csv(args$input_records, sep = "\t", stringsAsFactors = FALSE)

if (!(args$date_column %in% colnames(records_data))) {
    stop(paste("Date column not found in genome records input:", args$date_column), call. = FALSE)
}

record_dates <- as.Date(records_data[[args$date_column]], format = "%Y-%m-%d")
record_dates <- record_dates[!is.na(record_dates)]
record_dates_since_2000 <- record_dates[
    record_dates >= accumulation_start_date &
    record_dates <= plot_end_date
]

if (length(record_dates_since_2000) == 0) {
    stop("No valid genome record dates found since 2000.", call. = FALSE)
}

baseline_records <- sum(record_dates_since_2000 < plot_start_date)
plotted_record_dates <- record_dates_since_2000[
    record_dates_since_2000 >= plot_start_date
]

month_seq <- seq(
    from = plot_start_month,
    to = plot_end_month,
    by = "month"
)

monthly_counts <- table(cut(plotted_record_dates, "month"))

plot_records <- data.frame(DATE = month_seq, stringsAsFactors = FALSE)
plot_records$FREQ_RECORDS <- as.integer(monthly_counts[as.character(plot_records$DATE)])
plot_records$FREQ_RECORDS[is.na(plot_records$FREQ_RECORDS)] <- 0
plot_records$CUM_RECORDS <- baseline_records + cumsum(plot_records$FREQ_RECORDS)


# --- Read and Process Publications ---
pub_data <- read.csv(args$input_csv, sep = ",", header = FALSE, stringsAsFactors = FALSE)

if (ncol(pub_data) < 2) {
    stop("Publications input must contain at least two columns: publications, year.", call. = FALSE)
}

pub_data <- pub_data[, 1:2]
colnames(pub_data) <- c("publications", "year")

pub_data$year <- as.integer(pub_data$year)
pub_data$publications <- as.numeric(pub_data$publications)

pub_data <- pub_data[!is.na(pub_data$year) & !is.na(pub_data$publications), ]
pub_data <- pub_data[
    pub_data$year >= accumulation_start_year &
    pub_data$year <= plot_end_year
, ]

if (nrow(pub_data) == 0) {
    stop("No valid publication data found since 2000.", call. = FALSE)
}

pub_data <- pub_data %>%
    group_by(year) %>%
    summarize(publications = sum(publications), .groups = "drop")

baseline_publications <- sum(
    pub_data$publications[pub_data$year < plot_start_year],
    na.rm = TRUE
)

plot_publications <- data.frame(year = seq(plot_start_year, plot_end_year, by = 1))

plot_publications <- merge(plot_publications, pub_data, by = "year", all.x = TRUE)
plot_publications$publications[is.na(plot_publications$publications)] <- 0
plot_publications <- plot_publications[order(plot_publications$year), ]

plot_publications$CUM_PUBLICATIONS <- baseline_publications +
    cumsum(plot_publications$publications)
plot_publications$DATE <- as.Date(paste0(plot_publications$year, "-07-01"))


# --- Axis Scaling ---

max_records <- max(plot_records$CUM_RECORDS, na.rm = TRUE)
max_publications <- max(plot_publications$CUM_PUBLICATIONS, na.rm = TRUE)

if (max_records <= 0) {
    stop("Genome records cumulative total is zero; unable to plot.", call. = FALSE)
}

if (max_publications <= 0) {
    stop("Publication cumulative total is zero; unable to plot secondary axis.", call. = FALSE)
}

records_ylim <- ceiling(max_records * 1.05)

publications_ylim <- ceiling(max_publications * 1.05)

records_breaks <- pretty(c(0, records_ylim), n = 8)
records_breaks <- records_breaks[records_breaks >= 0 & records_breaks <= records_ylim]

scale_factor <- records_ylim / publications_ylim

plot_publications$CUM_PUBLICATIONS_SCALED <-
    plot_publications$CUM_PUBLICATIONS * scale_factor

publication_breaks <- pretty(c(0, publications_ylim), n = 8)
publication_breaks <- publication_breaks[
    publication_breaks >= 0 &
    publication_breaks <= publications_ylim
]

publication_breaks_scaled <- publication_breaks * scale_factor


# --- Calculate Average Yearly Growth (displayed years) ---

records_by_year <- plot_records %>%
    mutate(year = as.integer(format(DATE, "%Y"))) %>%
    group_by(year) %>%
    summarize(yearly_records = sum(FREQ_RECORDS), .groups = "drop")

avg_records_growth <- records_by_year %>%
    summarize(avg = mean(yearly_records, na.rm = TRUE)) %>%
    pull(avg)

avg_publications_growth <- plot_publications %>%
    summarize(avg = mean(publications, na.rm = TRUE)) %>%
    pull(avg)

format_growth <- function(value) {
    if (length(value) == 1 && !is.na(value)) {
        format(round(value, 1), big.mark = ",")
    } else {
        "n/a"
    }
}


# --- Compose Annotation Text (with blue publications line) ---
annotation_text <- paste0(
    "Avg. yearly growth (", plot_start_year, "-", plot_end_year, ") of",
    "<br>plastome records: ", format_growth(avg_records_growth),
    "<br><span style='color:#1f77b4;'>publications: ",
    format_growth(avg_publications_growth),
    "</span>"
)

# Measure text with a fileless device that supports the plot's font.
make_annotation_grob <- function(text) {
    svglite::svgstring(width = 7.2, height = 3.6)
    on.exit(grDevices::dev.off(), add = TRUE)
    gridtext::richtext_grob(
        text,
        x = unit(0.02, "npc"),
        y = unit(0.98, "npc"),
        hjust = 0,
        vjust = 1,
        halign = 1,
        gp = grid::gpar(fontsize = figure_annotation_size, fontfamily = figure_font, fontface = "bold", lineheight = 1.6),
        box_gp = grid::gpar(fill = NA, col = NA),
        padding = unit(c(6, 8, 6, 8), "pt")
    )
}

# Right-aligned label on a white box placed over the top-left panel corner
figure_annotation_size <- typography$annotation_size * 0.80
figure_tick_label_size <- typography$tick_label_size * 0.80
figure_axis_label_size <- typography$axis_label_size * 0.80
annotation_grob <- make_annotation_grob(annotation_text)


# --- Plot ---

year_boundaries <- unique(c(
    plot_start_date,
    as.Date(paste0(seq(plot_start_year, plot_end_year, by = 1), "-01-01")),
    plot_end_date
))
year_boundaries <- year_boundaries[
    year_boundaries >= plot_start_date & year_boundaries <= plot_end_date
]

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
        linewidth = 0.8
    ) +

    geom_point(
        data = plot_publications,
        aes(x = DATE, y = CUM_PUBLICATIONS_SCALED),
        color = "#1f77b4",
        size = 1.5
    ) +

    geom_rug(
        data = data.frame(DATE = year_boundaries),
        aes(x = DATE),
        sides = "b",
        outside = TRUE,
        length = unit(0.2, "cm")
    ) +

    annotation_custom(
        annotation_grob,
        xmin = as.Date(-Inf, origin = "1970-01-01"),
        xmax = as.Date(Inf, origin = "1970-01-01")
    ) +

    labs(
        x = "Year"
    ) +

    scale_x_date(
        breaks = as.Date(paste0(seq(plot_start_year, plot_end_year, by = 1), "-07-01")),
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

    theme_minimal(base_family = figure_font, base_size = figure_annotation_size) +
    theme(
        text = element_text(family = figure_font),
        axis.text = element_text(size = figure_tick_label_size),
        axis.text.x = element_text(angle = 0, hjust = 0.5, margin = margin(t = 8)),
        axis.ticks.x = element_blank(),
        axis.ticks.length = unit(0.2, "cm"),
        axis.title = element_text(size = figure_axis_label_size),
        axis.title.x = element_text(face = "bold", margin = margin(t = 12)),
        axis.title.y.left = element_text(face = "bold", margin = margin(r = 12)),
        axis.title.y.right = element_text(face = "bold", color = "#1f77b4", margin = margin(l = 12)),
        legend.text = element_text(size = typography$legend_size),
        axis.text.y.right = element_text(color = "#1f77b4"),
        plot.margin = unit(c(0.05, 0.05, 0.05, 0.05), "cm")
    )

# --- Save Plot ---

if (!capabilities("cairo")) {
    stop("Cairo support is required for the Figure 1 PDF export.", call. = FALSE)
}

svg_device <- if (requireNamespace("svglite", quietly = TRUE)) {
    svglite::svglite
} else {
    grDevices::svg
}

ggsave(file = svg_outfile, plot = myPlot, width = 7.2, height = 3.6, device = svg_device)
ggsave(file = png_outfile, plot = myPlot, width = 7.2, height = 3.6, dpi = 300)
ggsave(file = pdf_outfile, plot = myPlot, width = 7.2, height = 3.6, device = grDevices::cairo_pdf)
cat("Wrote files to ", relative_output_directory(dirname(output_base)), "\n", sep = "")

################################################################################