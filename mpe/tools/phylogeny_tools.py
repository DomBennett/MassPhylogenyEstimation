#! /bin/usr/env python
## D.J. Bennett
## 24/03/2014
"""
MPE phylogeny tools
"""

## Packages
import os,re,random
#from Bio import Phylo
#from Bio.Seq import Seq
from Bio.Align import MultipleSeqAlignment
from Bio.SeqRecord import SeqRecord
from Bio import Phylo
from Bio import AlignIO
import numpy as np
import dendropy as dp
from system_tools import TerminationPipe

## Old functions
# def renameTips(phylo, names):
# 	for each in phylo.get_terminals():
# 		try:
# 			each.name = names[each.name]["name"]
# 		except KeyError:
# 			pass
# 	return phylo

# def getBranchLengths(phylo):
# 	lens = []
# 	depths =  phylo.depths(unit_branch_lengths = True)
# 	for branch in depths.keys():
# 		if branch.branch_length:
# 			lens.append(branch.branch_length)
# 	return lens
	
# def goodPhylogenyTest(query, max_branch):
# 	lens = getBranchLengths(query)
# 	total_len = sum(lens)
# 	lens_bool = [e/total_len > max_branch for e in lens]
# 	if any(lens_bool):
# 		return False
# 	else:
# 		return True

# def phyloTest(query, ref_path, max_nsplits, max_branch):
# 	lens = getBranchLengths(query)
# 	total_len = sum(lens)
# 	lens_bool = [e/total_len > max_branch for e in lens]
# 	if any(lens_bool):
# 		return False
# 	elif max_nsplits:
# 		tax_tree = dp.Tree()
# 		tax_tree.read_from_path(ref_path, "newick")
# 		temp_tree = dp.Tree()
# 		Phylo.write(query, "temp_phylo.txt", 'newick')
# 		temp_tree.read_from_path("temp_phylo.txt", "newick")
# 		os.remove("temp_phylo.txt")
# 		# I don't think it's necessary for them to have the same number of taxa
# 		tax_list = [e for e in tax_tree.taxon_set]
# 		temp_list = [e for e in temp_tree.taxon_set]
# 		drop_list = [e1 for e1 in tax_list if e1.label not in [e2.label for e2 in temp_list]]
# 		tax_tree.prune_taxa(drop_list)
# 		print tax_tree.as_ascii_plot()
# 		# extract number of splits in the tax_tree not in temp_tree
# 		# http://pythonhosted.org/DendroPy/tutorial/treestats.html#frequency-of-a-split-in-a-collection-of-trees
# 		nsplits = tax_tree.false_positives_and_negatives(temp_tree)
# 		print "... [{0}] tax splits, [{1}] temp splits...".format(nsplits[0], nsplits[1])
# 		if nsplits[1] > max_nsplits:
# 			return False
# 		else:
# 			return True
# 	else:
# 		return True

def consensus(distribution_dir, consensus_dir, min_freq = 0.5, is_rooted = True,\
	trees_splits_encoded = False):
	"""Generate a rooted consensus tree from a distribution filepath"""
	trees = dp.TreeList()
	trees.read_from_path(distribution_dir, "newick", as_rooted = True)
	#https://groups.google.com/forum/#!topic/dendropy-users/iJ32ibnS5Bc
	sd = dp.treesplit.SplitDistribution(taxon_set=trees.taxon_set)
	sd.is_rooted = is_rooted
	tsum = dp.treesum.TreeSummarizer()
	tsum.count_splits_on_trees(trees,split_distribution=sd,\
		trees_splits_encoded=trees_splits_encoded)
	consensus = tsum.tree_from_splits(sd, min_freq = min_freq)
	consensus.write_to_path(os.path.join(consensus_dir), "newick")

def test(phylo, cutoff = 0.1):
	"""Return true if std(rrt.dist) < cutoff"""
	names = []
	for terminal in phylo.get_terminals():
		names.append(terminal.name)
	rtt_dists = []
	for name in names:
		rtt_dists.append(phylo.distance(name))
	if np.std(rtt_dists) < cutoff:
		return True
	else:
		return False

def getConstraintArg(constraint):
	"""Return constaint arg for RAxML"""
	# first write file
	with open(".constraint.tre", "w") as file:
		Phylo.write(constraint, file, "newick")
	# then return arg based on whether it bifurcates
	if constraint.is_bifurcating():
		return " -r .constraint.tre"
	else:
		return " -g .constraint.tre"

def genConstraintTree(alignment, taxontree_file):
	"""Return constraint tree based on taxon tree"""
	tip_names = []
	for record in alignment:
		tip_names.append(record.id)
	with open(taxontree_file, "r") as file:
		constraint = Phylo.read(file, "newick")
	constraint_tips = []
	for terminal in constraint.get_terminals():
		constraint_tips.append(terminal.name)
	tips_to_drop = [e for e in constraint_tips if not e in tip_names]
	for tip in tips_to_drop:
		constraint.prune(tip)
	return constraint

def concatenateAlignments(alignments):
	"""Take list of alignments for multiple genes.
Return single alignment with partitions."""
	if len(alignments) == 1:
		return alignments[0],False
	# Sort IDs
	alignment_ids = []
	for gene in alignments:
		gene_ids = []
		for rec in gene:
			gene_ids.append(rec.id)
		alignment_ids.append(gene_ids)
	all_ids = []
	[all_ids.extend(e) for e in alignment_ids]
	all_ids = list(set(all_ids))
	# Concatenate
	alignment = MultipleSeqAlignment([])
	for txid in all_ids:
		sequence = ""
		for i,gene in enumerate(alignments):
			if txid in alignment_ids[i]:
				sequence += gene[alignment_ids[i].index(txid)].seq
			else:
				sequence += "-" * gene.get_alignment_length()
		sequence = SeqRecord(sequence, id = txid, description =\
			"multigene sequence")
		alignment.append(sequence)
	# Get partitions
	lengths = [e.get_alignment_length() for e in alignments]
	partitions = [0]
	partitions.extend(list(np.cumsum(lengths)))
	return alignment,partitions

def getOutgroup(alignment, constraint):
	""""""
	spp = [e.id for e in alignment]
	if 'outgroup' in spp:
		return 'outgroup'
	# otherwise find the species(s) with the fewest shared taxonomic
	#  groups
	distances = [constraint.distance(e) for e in spp]
	index = [i for i,e in enumerate(distances) if e == min(distances)]
	# always choose the first, even if multiple species are.
	return spp[index[0]]

def RAxML(alignment, outgroup=None, partitions=None, constraint=None,\
	timeout=999999999):
	"""Adapted pG function: Generate phylogeny from alignment using 
RAxML (external program)."""
	input_file = '.phylogeny_in.phylip'
	output_file = '.phylogeny_out'
	file_line = ' -s ' + input_file + ' -n ' + output_file
	options = ' -p ' + str(random.randint(0,10000000)) + ' -T 2'
	if outgroup:
		options += ' -o ' + outgroup
	with open(input_file, "w") as file:
		AlignIO.write(alignment, file, "phylip-relaxed")
	if len(alignment) > 100:
		dnamodel = ' -m GTRCAT'
	else:
		dnamodel = ' -m GTRGAMMA'
	if partitions:
		with open(".partitions.txt", 'w') as f:
			for i in range(0, len(partitions)-1):
				f.write("DNA, position" + str(partitions[i]+1) + " = "\
				 + str(partitions[i]+1) + "-" + str(partitions[i+1]) + "\n")
		options += " -q " + ".partitions.txt"
	if constraint:
		options += constraint
	command_line = 'raxml' + file_line + dnamodel + options
	#print command_line
	pipe = TerminationPipe(command_line)
	pipe.run()
	if not pipe.failure:
		with open('RAxML_bestTree.' + output_file, "r") as file:
			tree = Phylo.read(file, "newick")	
		if constraint:
			os.remove('.constraint.tre')
		if partitions:
			os.remove(".partitions.txt")
		os.remove(input_file)
		all_files = os.listdir(os.getcwd())
		for each in all_files:
			if re.search("(RAxML)", each):
				os.remove(each)
			if re.search("\.reduced$", each):
				os.remove(each)
		return tree
	else:
		raise RuntimeError("Either phylogeny building program failed, or ran out of time")
