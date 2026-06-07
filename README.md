# Paper_Plastburstalign_Figures
Code for generating publication-quality figures and tables for the manuscript.

### Figure 1: Estimated yearly growth of plastid genome records and plastid genome publications
_Purpose: This figure shall illustrate that plastid genomics remains an active research field with sustained annual publication output and a rapidly expanding body of available genomes. The scale of available genomes now necessitates specialized software (namely ours!) that is capable of efficiently processing and analyzing thousands of plastid genomes simultaneously._

```bash
# Dependencies
Rscript -e "install.packages(c('argparse','ggplot2','ggrepel', 'ggtext', 'plyr','dplyr','svglite'), repos='https://cloud.r-project.org')"
# Figure creation
Rscript "CODE_AccumulationGraph__recordsAndPublications.R" --input-records "./input_data/output_script1.sorted.unique.tsv" --input-publications "./input_data/plastome_publications_per_year_2026-04-27.csv" --start-date "2020-01-01" --end-date "2026-12-31" --output "./VIZ_AccumulationGraphs/AccumulationGraph__recordsAndPublications"
```
![Combined accumulation graph](VIZ_AccumulationGraphs/AccumulationGraph__recordsAndPublications.png)

---

### Figure 2: Schematic overview of what the software does
_Purpose: This figure shall illustrate, for readers with no prior knowledge of the subject, the purpose and functionality of the software using a dataset of three simplistic plastid genomes._

```bash
python CODE_MethodOverview.py --output-dir ./VIZ_MethodOverview --output-name VIZ_MethodOverview
```
![Schematic of the script purpose](VIZ_MethodOverview/VIZ_MethodOverview.png)

---

### Table 1: Comparison of competitor software
_Purpose: This table may be the only table in the manuscript and shall provide a comparative overview of the capabilities of competing software packages alongside our own software. The comparison criteria should include, among others, the maximum number of input genomes supported, the number of genomes that can be analyzed within a fixed time period (e.g., one hour), the genomic features processed (CDSs, intergenic regions, introns/exons, or combinations thereof), the availability of the source code, the deployment model (server-based or executable on a personal computer), and the user interface type (command-line or graphical). This table should allow readers to quickly assess the functionality, accessibility, scalability, performance, and overall strengths and limitations of each software package._

| Tool                            | Publication               | Version tested | Extracts CDS, INT, and IGS | Dataset limitation                                         | Batch extraction | Batch alignment | Alignment software choice    | Source code            | Programming language | Deployment | Interface |
| ------------------------------- | ------------------------- | -------------- | -------------------------- | ---------------------------------------------------------- | ---------------- | --------------- | ---------------------------- | ---------------------- | -------------------- | ---------- | --------- |
| PhyloSuite                      | Zhang D. *et al.* 2019    | **Unclear**    | Yes                        | **Unclear**                                                | Yes              | Yes             | MAFFT, MUSCLE, MACSE         | Open-source            | **Unclear**          | Local      | GUI       |
| TBtools-II                      | Chen *et al.* 2023        | **Unclear**    | No (CDS only)              | **Unclear**                                                | Yes              | Limited         | External aligners            | Not publicly available | N/A                  | Local      | GUI       |
| OGU                             | Wu *et al.* 2024          | **Unclear**    | Yes                        | **Unclear**                                                | Yes              | Yes             | MAFFT                        | Open-source            | **Unclear**          | Local      | CLI + GUI |
| PartitioningExonsIntronsSpacers | de Mestier *et al.* 2025  | **Unclear**    | Yes                        | Yes; only 1 genome per run                                 | No               | No              | N/A                          | Open-source            | Python               | Local      | CLI       |
| PlastidHub                      | Zhang N.-N. *et al.* 2025 | **Unclear**    | Yes                        | Yes; 50 genomes (extraction), 150 genomes (alignment)      | Yes              | Yes             | **Unclear**                  | Open-source            | **Unclear** (Perl?)  | Web        | Web GUI   |
| PlastBurstAlign                 | This study                | 0.9.8          | Yes                        | No                                                         | Yes              | Yes             | MAFFT, Clustal Omega, MUSCLE | Open-source            | Python               | Local      | CLI       |

---

### Figure 3: Speed improvements through MPI implementation
_Purpose: This figure shall illustrate the substantial performance gains achieved through multithreading in our software and shall demonstrate that parallel processing is essential when analyzing datasets comprising thousands of genomes. This figure is the only one where all five datasets are compared. Any reader who sees this figure shall immediately recognize that multithreading provides substantial performance gains!_

```bash
python CODE_SpeedImprovements.py ./input_data/plastburst_benchmark_Final.csv ./VIZ_SpeedImprovements/PlastomeBurst_SpeedImprovements_AllMarkers
```
![Visualization of speed improvements](VIZ_SpeedImprovements/PlastomeBurst_SpeedImprovements_AllMarkers.png)

---

### Figure 4: Relative contributions of software and alignment multithreading to performance improvement
_Purpose: This figure shall demonstrate that simultaneous multithreading of both the general software workflow and the alignment software yields greater performance gains than multithreading either component individually._

```bash
Foo bar baz
```

Status: Needs to be made

---

### Figure 5: Optimization of thread allocation for runtime and memory efficiency
_Purpose: This figure shall inform users of the optimal thread settings for achieving the most favorable balance between reduced runtime and efficient RAM utilization._

```bash
python CODE_Visualize_peakMem_speedup_across_datasets.py ./input_data/benchmarking_results_combined.csv ./VIZ_peakMem_speedup/peakMem_speedup_across_datasets
```
![Visualization of peak memory and speedup](VIZ_peakMem_speedup/peakMem_speedup_across_datasets.png)

---

### Supplemental Figure 1: Overview of various optimizations
_Purpose: This figure gives us a detailed look at the various optimizations._

```bash
python CODE_Compare_factors_across_datasets.py ./input_data/benchmarking_results_combined.csv ./VIZ_Compare_factors_across_datasets/Comparing_factors_grid
```
![Visualization of speed improvements](VIZ_Compare_factors_across_datasets/Comparing_factors_grid.png)

---

### Supplemental Figure 2: Flowchart of Exon Splicing
_Purpose: This figure shall illustrate the exon splicing procedure implemented in the software, which is one of the more complex components of the software. It is intended to provide interested readers with a detailed understanding of how exon splicing is handled internally and will be of particular interest to algorithm nerds._

```bash
pdflatex -jobname="./VIZ_FlowchartExonSplicing/VIZ_FlowchartExonSplicing" CODE_FlowchartExonSplicing.tex
rm ./VIZ_FlowchartExonSplicing/VIZ_FlowchartExonSplicing.aux
rm ./VIZ_FlowchartExonSplicing/VIZ_FlowchartExonSplicing.log
convert -density 300 ./VIZ_FlowchartExonSplicing/VIZ_FlowchartExonSplicing.pdf ./VIZ_FlowchartExonSplicing/VIZ_FlowchartExonSplicing.png

## TO DO: Check if the same as the LaTeX version:
python CODE_FlowchartExonSplicing.py --output-dir ./VIZ_FlowchartExonSplicing --output-name VIZ_FlowchartExonSplicing_Python
```
![Flowchart of exon splicing](VIZ_FlowchartExonSplicing/VIZ_FlowchartExonSplicing.png)
