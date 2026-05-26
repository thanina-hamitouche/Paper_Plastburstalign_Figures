#!/usr/bin/R
# author: Michael Gruenstaeudl <m_gruenstaeudl@fhsu.edu>

library(argparse)
library(ggplot2)
library(sf)
library(dplyr)
library(rnaturalearth)

################################################################################
### ARGPARSE BLOCK ###

parser <- ArgumentParser(
    description = "Generate a world map of plastid genome records by country."
)
parser$add_argument("--input", required = TRUE, default = "./input/output_script1.sorted.unique.tsv", 
                    help = "Path to input frequency table file.")
parser$add_argument("--translate", required = TRUE, default = "./input/country_name_to_iso3.tsv", 
                    help = "Path to country name translation file.")
parser$add_argument("--output", default = "./output/chloropleth_map.svg",
                    help = "Output SVG filename (default: ./output/chloropleth_map.svg).")
parser$add_argument("--title", default = "Geographic origin of plastid genome records",
                    help = "Figure title (default: Geographic origin of plastid genome records).")
args <- parser$parse_args()

################################################################################

if (!file.exists(args$input)) {
    stop(paste("Input file not found:", args$input), call. = FALSE)
}

if (!file.exists(args$translate)) {
    stop(paste("Translation file not found:", args$translate), call. = FALSE)
}

raw <- readLines(args$input)

parse_line <- function(x) {
  line <- trimws(x)
  if (line == "") return(NULL)

  if (grepl(",", line, fixed = TRUE)) {
    parts <- strsplit(line, ",", fixed = TRUE)[[1]]
    if (length(parts) < 2) return(NULL)
    parts <- trimws(parts)
    count <- suppressWarnings(as.numeric(parts[length(parts)]))
    if (is.na(count)) return(NULL)
    country <- paste(parts[-length(parts)], collapse = ",")
  } else {
    parts <- strsplit(line, "\\s+")[[1]]
    if (length(parts) < 2) return(NULL)
    count <- suppressWarnings(as.numeric(parts[1]))
    if (is.na(count)) return(NULL)
    country <- paste(parts[-1], collapse = " ")
  }

  data.frame(count = count, country = country)
}

df_list <- lapply(raw, parse_line)
df_list <- Filter(Negate(is.null), df_list)
if (length(df_list) == 0) {
  stop(paste("No valid rows parsed from input file:", args$input), call. = FALSE)
}
df <- do.call(rbind, df_list)

df <- df %>% group_by(country) %>% summarise(count = sum(count, na.rm = TRUE))

################################################################################

world <- ne_countries(scale = "medium", returnclass = "sf")

world_data <- world %>%
  left_join(df, by = c("name" = "country"))

world_data$category <- cut(
  world_data$count,
  breaks = c(-Inf, 0, 9, 49, 100, Inf),
  labels = c("0", "1-10", "10-50", "50-100", ">100"),
  right = TRUE
)

################################################################################

p <- ggplot(world_data) +
  geom_sf(aes(fill = category), color = "black", size = 0.1) +
  scale_fill_manual(
    values = c(
      "0" = "white",
      "1-10" = "#c8c8c8",
      "10-50" = "#969696",
      "50-100" = "#4b4b4b",
      ">100" = "#000000"
    ),
    na.value = "white"
  ) +
  theme_minimal() +
  theme(
    panel.background = element_rect(fill = "white"),
    panel.grid = element_blank(),
    legend.title = element_blank()
  ) +
  labs(title = args$title)

################################################################################

svg_device <- if (requireNamespace("svglite", quietly = TRUE)) {
    svglite::svglite
} else {
    grDevices::svg
}
ggsave(file=args$output, plot=p, width=10, height=6, device=svg_device)

################################################################################