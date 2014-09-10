#! /bin/usr/env python
## D.J. Bennett
## 26/05/2014
"""
Test phylogeny stage.
"""

import unittest,os,shutil,pickle
from mpe.stages import phylogeny_stage
from Bio import AlignIO
from Bio import Phylo
from cStringIO import StringIO

## Dirs
working_dir = os.path.dirname(__file__)

## Functions
class AlignmentSeq(object):
	def __init__(self, name):
		self.id = name

def genAlignment(names):
	# little function that generates a list of sequences
	#  looks like an alignment to getOutgroup
	return [AlignmentSeq(e) for e in names]

## Dummies
def dummy_concatenateAlignments(alignments):
	return genAlignment(['outgroup', 'B', 'C', 'D', 'E']),None

def dummy_genConstraintTree(alignment, path):
	treedata = "(outgroup, (B, C), (D, E))"
	handle = StringIO(treedata)
	tree = Phylo.read(handle, "newick")
	return tree

def dummy_getConstraintArg(constraint):
	return None

def dummy_RAxML(alignment,constraint,outgroup,partitions):
	treedata = "(outgroup, (B, C), (D, E))"
	handle = StringIO(treedata)
	tree = Phylo.read(handle, "newick")
	return tree
	
def dummy_test(phylogeny, maxpedge):
	return True

## Test data
with open(os.path.join(working_dir, 'data','test_alignment_ref.faa'),\
	'r') as file:
	alignment = AlignIO.read(file, 'fasta')

paradict = {'ntrees':1,'maxtrys':1,'maxrttsd':0.5}


class PhylogenyStageTestSuite(unittest.TestCase):

	def setUp(self):
		# stub out
		self.true_concatenateAlignments = phylogeny_stage.ptools.concatenateAlignments
		self.true_genConstraintTree = phylogeny_stage.ptools.genConstraintTree
		self.true_getConstraintArg = phylogeny_stage.ptools.getConstraintArg
		self.true_RAxML = phylogeny_stage.ptools.RAxML
		self.true_test = phylogeny_stage.ptools.test
		phylogeny_stage.ptools.concatenateAlignments = dummy_concatenateAlignments
		phylogeny_stage.ptools.genConstraintTree = dummy_genConstraintTree
		phylogeny_stage.ptools.getConstraintArg = dummy_getConstraintArg
		phylogeny_stage.ptools.RAxML = dummy_RAxML
		phylogeny_stage.ptools.test = dummy_test
		# create input data
		with open(".paradict.p", "wb") as file:
			pickle.dump(paradict, file)
		os.mkdir('3_alignment')
		os.mkdir('4_phylogeny')
		os.mkdir(os.path.join('3_alignment','COI'))
		os.mkdir(os.path.join('3_alignment','rbcl'))
		with open(os.path.join('3_alignment', 'rbcl',\
			'test_alignment_rbl.faa'), 'w') as file:
			count = AlignIO.write(alignment, file, "fasta")
			del count
		with open(os.path.join('3_alignment', 'COI',\
			'test_alignment_COI.faa'), 'w') as file:
			count = AlignIO.write(alignment, file, "fasta")
			del count

	def tearDown(self):
		##TODO: Generalise and repeat this for all tearDowns
		# remove all files potentially generated by phylogeny stage
		phylogeny_files = ['.paradict.p']
		while phylogeny_files:
			try:
				phylogeny_file = phylogeny_files.pop()
				os.remove(phylogeny_file)
			except OSError:
				pass
		# remove all folders potentially generated by phylogeny stage
		phylogeny_folders = ['3_alignment', '4_phylogeny']
		while phylogeny_folders:
			try:
				phylogeny_folder = phylogeny_folders.pop()
				shutil.rmtree(phylogeny_folder)
			except OSError:
				pass
		#stub in
		phylogeny_stage.ptools.concatenateAlignments = self.true_concatenateAlignments
		phylogeny_stage.ptools.genConstraintTree = self.true_genConstraintTree
		phylogeny_stage.ptools.getConstraintArg = self.true_getConstraintArg
		phylogeny_stage.ptools.RAxML = self.true_RAxML
		phylogeny_stage.ptools.test = self.true_test

	def test_phylogeny_stage(self):
		# run
		res = phylogeny_stage.run()
		# clean dir
		os.remove(os.path.join('4_phylogeny', 'distribution.tre'))
		os.remove(os.path.join('4_phylogeny', 'consensus.tre'))
		os.rmdir('4_phylogeny')
		# assert
		self.assertIsNone(res)

if __name__ == '__main__':
    unittest.main()