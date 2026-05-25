#!/bin/bash

# Global variables
green='\e[1;32m'
yellow='\e[0;33m'
nocolor='\e[0m'

TITLE="simple_location_mining_via_entrez.sh"
DESCRIPTION="Shell script to extract location information from records stored on NCBI Nucleotide"
AUTHOR="Michael Gruenstaeudl, PhD"
CONTACT="m_gruenstaeudl@fhsu.edu"
VERSION="2026.04.27"
USAGE="bash <this_script> <input_file> <output_location_data> <output_frequency_table>"

################################################################################

# STEP 1: INTRO DISPLAY

echo ""
echo -e " ${green}Title: $TITLE | Version: $VERSION | Author: $AUTHOR${nocolor}"
echo -e " ${yellow}Usage: $USAGE${nocolor}"
echo ""

################################################################################

if [ $# -lt 1 ]; then
    echo "Usage: $0 <output_file>" >&2
    exit 1
fi

OUTFILE="$1"

QUERY="(((plastid genome[TITLE] OR chloroplast genome[TITLE] OR plastome[TITLE]) OR (plastid genomKEYWKEYW] OR chloroplast genomKEYWKEYW] OR plastomKEYWKEYW])) AND (phylogenomic[TITLE] OR phylogenomicKEYWKEYW]))"

esearch -db pubmed -query "$QUERY" | \
efetch -format docsum | \
grep -oP "(?<=<PubDate>)[^<]+" | \
awk '{print $1}' | sort | uniq -c | \
awk '{print $1","$2}' | \
sort -t ',' -k2 -rn > "$OUTFILE"
