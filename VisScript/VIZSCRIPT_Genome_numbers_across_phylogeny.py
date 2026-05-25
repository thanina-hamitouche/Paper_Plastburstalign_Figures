#!/usr/bin/env python3
# author: Michael Gruenstaeudl <m_gruenstaeudl@fhsu.edu>

import argparse
import csv
import logging
import os.path
import time

import coloredlogs
import numpy as np
import pandas as pd
from ete4 import ETE_DATA_HOME, NCBITaxa, Tree
from ete4.treeview import NodeStyle, RectFace, TextFace, TreeStyle

################################################################################

__author__ = "Michael Gruenstaeudl <m_gruenstaeudl@fhsu.edu>"
__copyright__ = "Copyright (C) 2021-2026 Michael Gruenstaeudl"
__info__ = (
    "Prune angiosperm phylogenetic tree to family level and annotate "
    "leaves with counts of avaible plastid genome entries in "
    "NCBI GenBank."
)
__version__ = "2021.10.07"

################################################################################

# Qualitative palette derived from ColorBrewer2 Set3 (12 colors) extended with Paired (8 colors)
_PALETTE = [
    "#8dd3c7", "#ffffb3", "#bebada", "#fb8072", "#80b1d3",
    "#fdb462", "#b3de69", "#fccde5", "#d9d9d9", "#bc80bd",
    "#ccebc5", "#ffed6f", "#a6cee3", "#1f78b4", "#b2df8a",
    "#33a02c", "#fb9a99", "#e31a1c", "#fdbf6f", "#ff7f00",
]

################################################################################


def collate_species_into_families(species_set, ncbi_db):
    """
    Constructs a dictionary from a set of species names where each family name key has a set of species name values assigned.
    Params:
     - species_set: the set of species that is to be assigned to families
     - ncbi_db: a NCBITaxa object to lookup a species' family name
    """
    species_per_family = {}
    species_taxids = ncbi_db.get_name_translator(species_set)
    for species, taxid in species_taxids.items():
        fam_name = get_family_from_lineage(ncbi_db.get_taxid_translator(ncbi_db.get_lineage(taxid[0])))
        if fam_name:
            if fam_name in species_per_family:
                species_per_family[fam_name].add(species)
            else:
                species_per_family[fam_name] = set([species])
    return species_per_family


def count_species_per_families(species_set, ncbi_db):
    """
    Constructs a dictionary from a set of species names where each family name key has the total number of species names assigned.
    Params:
     - species_set: the set of species that is to be assigned to families
     - ncbi_db: a NCBITaxa object to lookup a species' family name
    """
    species_count_per_family = {}
    species_taxids = ncbi_db.get_name_translator(species_set)
    for species, taxid in species_taxids.items():
        fam_name = get_family_from_lineage(ncbi_db.get_taxid_translator(ncbi_db.get_lineage(taxid[0])))
        if fam_name:
            if fam_name in species_count_per_family:
                species_count_per_family[fam_name] += 1
            else:
                species_count_per_family[fam_name] = 0
    return species_count_per_family


def get_species_from_table(fp_table):
    """
    Reads a csv file and returns the "organism" column as numpy array
    Params:
     - fp_table: file path to csv file
    """
    plastome_table = pd.read_csv(fp_table, sep="\t", index_col=0)
    species_list = plastome_table["ORGANISM"].to_numpy()
    return species_list


def get_family_from_lineage(lineage):
    """
    Returns the family (taxonomic rank) name from a lineage
    Params:
     - lineage: dict with NCBI tax id as key and corresponding taxonomic name as value
    """
    fam_name = None
    for k, v in lineage.items():
        rankinfo = NCBITaxa().get_rank([k])
        if [*rankinfo.values()][0] == "family":
            fam_name = v
    return fam_name


def get_families_from_lineages(lineages):
    """
    Returns a list of families
    Params:
     - lineages: dict with NCBI tax id as key and corresponding taxonomic name as value
    """
    myfamilies = []
    for k, v in lineages.items():
        rankinfo = NCBITaxa().get_rank([k])
        if [*rankinfo.values()][0] == "family":
            myfamilies.append(v)
    return myfamilies


def get_node_of_group_of_interest(tree, taxid, ncbi_db):
    """
    Identified the node number given the taxid of a group of interest
    NOTE: only works if input tree has families as leaves!
    Params:
     - tree: an ete3 Tree with species-level taxonomic names as leaf names
     - taxid: the NCBI taxid of a group of interest
     - ncbi_db: a NCBITaxa object to lookup a species' family name
    """
    ancestor_taxid_list = []
    # First, get all descendants of an internal node (taxid); then, get all ancestors of those descendants
    for descendant in ncbi_db.get_descendant_taxa(taxid):
        ancestor_taxid_list += ncbi_db.get_lineage(descendant)

    # Make taxon list unique and translate to real names
    unique_ancestor_names = ncbi_db.get_taxid_translator(set(ancestor_taxid_list))

    # Filter out only the families from list
    families_in_group = get_families_from_lineages(unique_ancestor_names)
    if isinstance(families_in_group, str):
        families_in_group = [families_in_group]

    # Get all leaf names (at this point: family names)
    families_in_tree = [leaf.name for leaf in tree.leaves()]

    # Get all families that are in both group and tree
    families_in_group_and_tree = list(set(families_in_group).intersection(set(families_in_tree)))

    # Get node of interest (noi)
    noi = tree.common_ancestor(families_in_group_and_tree)
    return noi


def prune_to_family_level(inTree, species_per_family):
    """
    Prunes a tree from species-level leaves to family-level leaves
    Params:
     - inTree: an ete3 Tree with species-level taxonomic names as leaf names
     - species_per_family: dict where each family name key has a set of species name values assigned
    """
    # TODO: Check that detaching a child does not detach leaves of a different family
    # Probably an issue with some common ancestors being identified as close to the root
    fam_nodes = []
    for family, species in species_per_family.items():
        if len(species) == 1:
            # If there is only one species in a family, simply rename the leaf
            fam_node = next(inTree.search_leaves_by_name(list(species)[0].replace(" ", "_")))
            fam_node.name = family
            fam_nodes.append(fam_node)
        else:
            # If there are multiple species in family, rename the tree node
            fam_node = inTree.common_ancestor([spec.replace(" ", "_") for spec in species])
            fam_node.name = family
            fam_nodes.append(fam_node)

    inTree.prune([f_node.name for f_node in fam_nodes])
    # cmd 'prune' prunes the topology of a tree to conserve only the selected list of internal leaf nodes


def attach_text_faces_to_tree(tree, genome_count_per_family, species_count_per_family):
    """
    Attaches TextFaces to tree leaves with plastid genome counts per leaf (=family) and leaf name
    Params:
     - tree: ete3 tree with family names as leaves
     - genome_count_per_family: dict with key = family name, value = number of sequenced plastid genomes for that family
     - species_count_per_family
    """
    for leaf in tree.leaves():
        leaf.add_face(TextFace(str(leaf.name)), column=0, position="aligned")
        if leaf.name in genome_count_per_family:
            leaf.add_face(
                TextFace("(" + str(species_count_per_family[leaf.name]) + "/" + str(genome_count_per_family[leaf.name]) + ")"),
                column=1,
                position="aligned",
            )
        else:
            leaf.add_face(TextFace("(" + str(species_count_per_family[leaf.name]) + "/0)"), column=1, position="aligned")


def attach_rect_faces_to_tree(tree, genome_count_per_family, log):
    """
    Attaches a RectFace to each applicable tree leave, with the height representing plastid genome counts per leaf (=family)
    Params:
     - tree: ete3 tree with family names as leaves
     - genome_count_per_family: dict with key = family name, value = number of sequenced plastid genomes for that family
     - log: logger
    """
    for leaf in tree.leaves():
        if leaf.name in genome_count_per_family:
            leaf.add_face(
                RectFace(width=genome_count_per_family[leaf.name] * 10, height=3, fgcolor="red", bgcolor="red"),
                column=1,
                position="aligned",
            )
        else:
            log.warning("Family '%s' not in list 'genome_count_per_family'. Not adding rect face for this family ...\n" % (leaf.name))


################################################################################


def main(args):
    # STEP 1: Set up logger
    log = logging.getLogger(__name__)
    coloredlogs.install(fmt="%(asctime)s [%(levelname)s] %(message)s", level="DEBUG", logger=log)

    # STEP 2: Retrieve and/or update localized NCBI Taxonomy database
    ncbi = NCBITaxa()
    if (time.time() - os.path.getmtime(ETE_DATA_HOME + "/taxa.sqlite")) > 604800:
        ncbi.update_taxonomy_database()

    # STEP 3: Tree operations

    # Step 3.1 Read tree from input file
    log.info("Loading tree...")
    inTree = Tree(open(args.treefn), parser=5)

    # STEP 3.2: Extracting species names from tree
    log.info("Extracting all unique species (leaf) names from tree...")
    species_from_tree = set()
    for leafname in inTree.leaf_names():
        species_from_tree.add(leafname.replace("_", " "))

    # STEP 3.3: Collating families from tree data, extracting and counting species per family
    log.info("Collating families from tree data, extracting and counting species per family...")
    families_with_spec_names_from_tree = collate_species_into_families(species_from_tree, ncbi)

    # STEP 3.4: Prune the tree
    log.info("Pruning tree to family level...")
    prune_to_family_level(inTree, families_with_spec_names_from_tree)

    # STEP 4: Table operations
    #         Calculate counts of species per family and plastid genome entries per family
    #         and attach them to the tree leaves

    # STEP 4.1: Read plastid genome information from input table, extracting species names from table
    log.info("Extracting all unique species names from table...")
    species_from_table = set(get_species_from_table(args.tablefn))

    # STEP 4.2: Collating families from table data, counting species per family
    log.info("Collating families from table data, counting species per family...")
    families_with_spec_numbers_from_table = count_species_per_families(species_from_table, ncbi)

    # STEP 5: Comparison tree data to table data
    # STEP 5.1: Count plastid genome entries per family
    log.info("Counting plastid genome entries per family in tree...")
    genome_count_per_family = {}
    for k, v in families_with_spec_numbers_from_table.items():
        if k in families_with_spec_names_from_tree.keys():
            genome_count_per_family[k] = v

    sorted_genome_count_per_family = dict(
        sorted(genome_count_per_family.items(), key=lambda item: item[1], reverse=True)
    )

    # STEP 5.2: Write plastid genome numbers per family to file
    log.info("Writing plastid genome numbers per family to file...")
    with open(args.csvfn, "w") as csvfile:
        writer = csv.writer(csvfile, dialect="excel")
        for k, v in sorted_genome_count_per_family.items():
            writer.writerow((k, v))

    # STEP 6: Tree customizations

    # STEP 6.1: Attach counts to tree leaves
    log.info("Attaching genome counts to tree...")

    # Log-transform (base of 10) the genome counts
    transf_array = np.log10([*sorted_genome_count_per_family.values()])
    transf_array = np.where(np.isneginf(transf_array), 0, transf_array)
    for i in range(0, len(sorted_genome_count_per_family)):
        sorted_genome_count_per_family[[*sorted_genome_count_per_family.keys()][i]] = transf_array[i]

    # Attach counts to tree
    attach_rect_faces_to_tree(inTree, sorted_genome_count_per_family, log)

    # STEP 6.2: Set TreeStyle
    ts = TreeStyle()
    ts.mode = "c"
    ts.draw_guiding_lines = False
    ts.show_leaf_name = False

    # STEP 6.3: Set NodeStyle
    nstyle = NodeStyle()
    nstyle["size"] = 0
    for n in inTree.traverse():
        n.set_style(nstyle)

    # STEP 6.4: Set Node backgrounds
    # See: http://etetoolkit.org/docs/latest/tutorial/tutorial_drawing.html#node-backgrounds
    log.info("Setting clade backgrounds...")

    groups_of_interest = {
        "Buxales": 280577,
        "Ceratophyllales": 91811,
        "Chloranthales": 261008,
        "Gunnerales": 232382,
        "asterids": 71274,
        "Berberidopsidales": 403664,
        "Caryophyllales": 3524,
        "Dilleniales": 403665,
        "rosids": 71275,
        "Santalales": 41947,
        "Saxifragales": 41946,
        "Liliopsida": 4447,
        "Magnoliidae": 232347,
        "Proteales": 232378,
        "Ranunculales": 41768,
        "Trochodendrales": 400839,
        "Nymphaeales": 261007,
    }

    # Assign colors automatically from palette, cycling if more groups than colors
    group_colors = [
        _PALETTE[i % len(_PALETTE)] for i in range(len(groups_of_interest))
    ]

    node_bgs = {}
    for (k, taxid), color in zip(groups_of_interest.items(), group_colors):
        noi = get_node_of_group_of_interest(inTree, taxid, ncbi)
        if noi.is_root:
            continue

        noi_nodestyle = NodeStyle()
        noi_nodestyle["bgcolor"] = color
        noi_nodestyle["size"] = 0
        noi.set_style(noi_nodestyle)
        noi.add_face(TextFace(str(k), fsize=12), column=0, position="float-behind")
        node_bgs[k] = noi

    # STEP 7: Rendering tree
    log.info("Rendering tree...")
    inTree.render(args.outfn, tree_style=ts)


################################################################################

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="  --  ".join([__author__, __copyright__, __info__, __version__])
    )
    parser.add_argument(
        "-i",
        "--treefn",
        type=str,
        required=True,
        help="path to input tree file. File has to be in Newick format 5 as specified in http://etetoolkit.org/docs/latest/tutorial/tutorial_trees.html#reading-and-writing-newick-trees",
    )
    parser.add_argument(
        "-t",
        "--tablefn",
        type=str,
        required=True,
        help="path to .csv file containing information on plastid genomes available in NCBI GenBank",
    )
    parser.add_argument(
        "-o",
        "--outfn",
        type=str,
        required=True,
        help="path to vizualization output file (SVG, PDF and PNG, depending on outfile name)",
    )
    parser.add_argument(
        "-c",
        "--csvfn",
        type=str,
        required=False,
        default="sorted_genome_count_per_family.csv",
        help="path to supplementary output file (in CSV format)",
    )
    args = parser.parse_args()
    main(args)
