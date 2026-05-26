# Paper_Plastburstalign_Figures
Code for generating publication-quality figures and tables for the manuscript.

### Accumulation graphs
```bash
Rscript -e "install.packages(c('argparse','ggplot2','plyr','dplyr','svglite'), repos='https://cloud.r-project.org')"
```

#### By genome record
```bash
Rscript "./CODE_a1_AccumulationGraph__genomeRecords.R" --input "./input_data/output_script1.sorted.unique.tsv" --output "./VIZ_a_AccumulationGraphs/AccumulationGraph__genomeRecords"
```
![Accumulation graph by genome records](VIZ_a_AccumulationGraphs/AccumulationGraph__genomeRecords.png)

#### By publications
```bash
Rscript "./CODE_a2_AccumulationGraph__publications.R" --input "./input_data/plastome_publications_per_year_2026-04-27.csv" --output "./VIZ_a_AccumulationGraphs/AccumulationGraph__publications"
```
![Accumulation graph by publications](VIZ_a_AccumulationGraphs/AccumulationGraph__publications.png)

### Method overview - Schematic
```bash
Foo bar baz
```
![Schematic of the script purpose](VIZ_b_MethodOverview/VIZ_MethodOverview_manually-corrected_2025-01-04.png)

### Exon Splicing - Flowchart
```bash
Foo bar baz
```
![Flowchart of exon splicing](VIZ_c_FlowchartExonSplicing/VIZ_FlowchartExonSplicing.png)

### Speed Improvements
```bash
Foo bar baz
```
![Visualization of speed improvements](VIZ_d_SpeedImprovements/SpeedImprovements_AllMarkers.png)
