#!/bin/bash
set -euo pipefail

# Global variables
green='\e[1;32m'
yellow='\e[0;33m'
nocolor='\e[0m'

TITLE="pubmed_plastid_phylogenomics_by_year.sh"
DESCRIPTION="Count PubMed publications on plastid phylogenomics by publication year"
AUTHOR="Michael Gruenstaeudl, PhD"
VERSION="2026.10.25"
USAGE="bash $0 <output_file.csv>"

################################################################################
# STEP 1: INTRO DISPLAY

printf '\n%bTitle: %s | Version: %s | Author: %s%b\n' \
    "$green" "$TITLE" "$VERSION" "$AUTHOR" "$nocolor"
printf '%b%s%b\n' "$yellow" "$DESCRIPTION" "$nocolor"
printf '%bUsage: %s%b\n\n' "$yellow" "$USAGE" "$nocolor"

################################################################################
# STEP 2: VALIDATE ARGUMENTS AND DEPENDENCIES

if [ "$#" -ne 1 ]; then
    printf 'Usage: %s\n' "$USAGE" >&2
    exit 1
fi

for program in esearch efetch xtract; do
    if ! command -v "$program" >/dev/null 2>&1; then
        printf 'Error: required program not found: %s\n' "$program" >&2
        exit 1
    fi
done

OUTFILE="$1"

# Use a temporary file to preserve any existing output if the query fails.
TMPFILE=$(mktemp)
trap 'rm -f "$TMPFILE"' EXIT

################################################################################
# STEP 3: SEARCH PUBMED AND COUNT PUBLICATIONS BY YEAR

# Keep the query on one line.
QUERY='("plastid genome"[tiab] OR "chloroplast genome"[tiab] OR plastome[tiab]) AND phylogenomic*[tiab]'

if ! esearch -db pubmed \
        -query "$QUERY" \
        -datetype PDAT \
        -mindate 2000/01/01 \
        -maxdate 2025/12/31 |
    efetch -format docsum |
    xtract -pattern DocumentSummary -element PubDate |
    awk 'match($0, /^[0-9]{4}/) {print substr($0, 1, 4)}' |
    sort |
    uniq -c |
    awk '{print $1 "," $2}' |
    sort -t ',' -k2,2nr > "$TMPFILE"
then
    printf 'Error: PubMed retrieval failed. Output was not updated.\n' >&2
    exit 1
fi

if [ ! -s "$TMPFILE" ]; then
    printf 'No publication years retrieved. Check the query and EDirect messages.\n' >&2
    exit 1
fi

mv -- "$TMPFILE" "$OUTFILE"

################################################################################
# STEP 4: DISPLAY TOTAL

awk -F ',' '{total += $1}
    END {printf "Total publications: %d\n", total}' "$OUTFILE"

printf 'Results saved to: %s\n' "$OUTFILE"
