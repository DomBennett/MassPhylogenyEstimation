#! /bin/usr/env python
# D.J. Bennett
# 26/05/2014
"""
Tests for phylogeny tools.
"""

import unittest
import pickle
import os
import shutil
import re
from copy import deepcopy
from Bio import Phylo
from Bio import AlignIO
import pglt.tools.phylogeny_tools as ptools

# DIRS
working_dir = os.path.dirname(__file__)


# MOCK DATA
# TODO get more test data with known frames
# two alignments for two genes
# N.B. I split the original concatenated alignment +1bp out. The first
#  alignment should really be 1760 and the second 1381, not 1761 and 1380.
with open(os.path.join(working_dir, "data", "test_alignment.p"), "rb") as file:
    test_alignment = pickle.load(file)

# super alignment of both genes
with open(os.path.join(working_dir, "data", "test_alignments.p"), "rb") \
        as file:
    test_alignments = pickle.load(file)

with open(os.path.join(working_dir, "data", "test_phylo.p"), "rb") as file:
    test_phylo = pickle.load(file)

with open(os.path.join(working_dir, "data", "test_constraint.tre"), "r") \
        as file:
    constraint = Phylo.read(file, 'newick')

# generate fake dict
genedict = {'gene1': {'partition': 'False'},
            'gene2': {'partition': 'False'}}


# DUMMIES
class dummy_Logger(object):

    def __init__(self):
        pass

    def info(self, msg):
        pass

    def debug(self, msg):
        pass


def dummy_RAxML(alignment, wd, logger, threads, outgroup=None, partitions=None,
                constraint=None, timeout=999999999):
    return test_phylo


class AlignmentSeq(object):

    def __init__(self, name):
        self.id = name


# FUNCTIONS
def genAlignment(names):
    # little function that generates a list of sequences
    #  looks like an alignment to getOutgroup
    return [AlignmentSeq(e) for e in names]


class PhylogenyTestSuite(unittest.TestCase):

    def setUp(self):
        self.wd = os.getcwd()
        self.logger = dummy_Logger()
        # stub out
        self.true_RAxML = ptools.RAxML
        ptools.RAxML = dummy_RAxML
        # generate fake alignment and phylogeny folders
        clusters = ['gene1_cluster0', 'gene2_cluster0']
        indir = '3_alignment'
        outdir = '4_phylogeny'
        os.mkdir(indir)
        os.mkdir(outdir)
        j = 0
        for cluster in clusters:
            os.mkdir(os.path.join(indir, cluster))
            for i in range(10):
                fname = '{0}_testalignment{1}.faa'.format(i, j)
                directory = os.path.join(indir, cluster, fname)
                with open(directory, "w") as file:
                    AlignIO.write(test_alignments[j], file, "fasta")
            j += 1
        with open(os.path.join(outdir, "taxontree.tre"), "w") as file:
            Phylo.write(test_phylo, file, "newick")
        self.alignment_store = ptools.AlignmentStore(clusters=clusters,
                                                     genedict=genedict,
                                                     allrankids=[],
                                                     indir=indir,
                                                     logger=self.logger)
        self.generator = ptools.Generator(alignment_store=self.alignment_store,
                                          rttstat=0.5, outdir=outdir,
                                          maxtrys=10, logger=self.logger)
        self.phylo = test_phylo
        self.carg = ' -g constraint.tre'
        self.parg = ' -q partitions.txt'
        self.constraint = constraint
        self.poutgroups = ['Ignatius_tetrasporus', 'Oltmannsiellopsis_viridis',
                           'Ulothrix_zonata']
        self.partition_text = 'DNA, gene1 = 1-1761\nDNA, gene2 = 1762-3141\n'

    def tearDown(self):
        # stub in
        ptools.RAxML = self.true_RAxML
        # remove all files potentially generated by ptools
        ptool_files = ['constraint.tre', 'distribution.tre', 'consensus.tre',
                       '.phylogeny_in.phylip.reduced',
                       'RAxML_info..phylogeny_out', '.phylogeny_in.phylip',
                       '.partitions.txt.reduced', 'partitions.txt',
                       'RAxML_bestTree..phylogeny_out',
                       'RAxML_log..phylogeny_out',
                       'RAxML_result..phylogeny_out']
        while ptool_files:
            try:
                ptool_file = ptool_files.pop()
                os.remove(ptool_file)
            except OSError:
                pass
        phylogeny_folders = ['3_alignment', '4_phylogeny']
        while phylogeny_folders:
            try:
                phylogeny_folder = phylogeny_folders.pop()
                shutil.rmtree(phylogeny_folder)
            except OSError:
                pass

    def test_stop_codon_retriever(self):
        # eukaryota, vertebrate, tetrapod, mammal, boreoeutherian, primate,hsap
        human_ids = [2759, 7742, 32523, 40674, 1437010, 9443, 9606]
        # eukaryota, diplomonad, Hexamitidae, h. inflata
        hinflata_ids = [2759, 5738, 5739, 28002]
        retriever = ptools.StopCodonRetriever()
        human_pattern = retriever.pattern(ids=human_ids, logger=self.logger)
        hinflata_pattern = retriever.pattern(ids=hinflata_ids,
                                             logger=self.logger)
        # humans are vertebrates
        self.assertEqual(human_pattern[0].pattern, '(taa|tag|aga|agg)')
        # h.inflata are ciliates
        self.assertEqual(hinflata_pattern[0].pattern, 'tag')

    def test_alignment_store(self):
        # check it works
        alignments, stops = self.alignment_store.pull()
        # should return one of each test alignments
        alens = [len(e) for e in alignments]
        self.assertTrue(len(test_alignments[0]) in alens)
        self.assertTrue(len(test_alignments[1]) in alens)
        self.assertEqual(stops, stops)

    def test_generator_private_test(self):
        # the test phylo should pass the test
        self.assertTrue(self.generator._test(phylogeny=self.phylo))
        # make one branch really big, new phylo should fail
        bad_phylo = deepcopy(self.phylo)
        bad_phylo.get_terminals()[0].branch_length = 100000
        self.assertIsNone(self.generator._test(phylogeny=bad_phylo))

    def test_generator_private_concatenate(self):
        # give it the test_alignments and a bigger alignment should return
        full_length = test_alignments[0].get_alignment_length() + \
            test_alignments[1].get_alignment_length()
        alignment = self.generator._concatenate(test_alignments)
        self.assertEqual(alignment.get_alignment_length(), full_length)

    def test_generator_private_constraint(self):
        # 4 tips in taxon tree not present in alignment
        carg = self.generator._constraint(test_alignment)
        self.assertTrue(os.path.isfile('constraint.tre'))
        with open("constraint.tre", "r") as file:
            constraint = Phylo.read(file, "newick")
        self.assertEqual(len(constraint.get_terminals()), 11)
        self.assertEqual(carg, self.carg)

    def test_generator_private_outgroup(self):
        # check with outgroup
        alignment = genAlignment(['outgroup', 'F', 'B', 'H'])
        res = self.generator._outgroup(alignment)
        self.assertEqual(res, 'outgroup')
        # try without outgroup
        with open(".constraint.tre", "w") as file:
            Phylo.write(constraint, file, "newick")
        res = self.generator._outgroup(test_alignment)
        # should return one of the basal tips from the constraint
        self.assertTrue(res in self.poutgroups)

    def test_generator_private_findorf(self):
        # find frames in test alignments[1] -- rcbl
        # N.B. test_alignments[0] is SSU which is RNA
        # this is standard code for stop codon
        stops = (re.compile('(taa|tag)', flags=re.IGNORECASE),
                 re.compile('(tta|cta)', flags=re.IGNORECASE))
        alignment, res = self.generator._findORF(test_alignments[1],
                                                 stop=stops)
        self.assertTrue(res)
        # find frames using nonsense stop patterns
        #  -- no frames will be found
        stops = (re.compile('(tct|aca)', flags=re.IGNORECASE),
                 re.compile('(aga|tgt)', flags=re.IGNORECASE))
        alignment, res = self.generator._findORF(test_alignments[0],
                                                 stop=stops)
        self.assertFalse(res)

    def test_generator_private_partition(self):
        # create partition text for the two genes, make sure they're correct
        alignment, parg = self.generator._partition(test_alignments,
                                                    [None, None])
        self.assertTrue(os.path.isfile('partitions.txt'))
        with open('partitions.txt', 'r') as file:
            text = file.read()
        self.assertEqual(text, self.partition_text)
        self.assertEqual(parg, self.parg)
        # TODO: repeat above for codon partitioned alignments

    def test_generator_private_setup(self):
        # test concatenate, contstraint, outgroup and partition in one
        alignment, carg, outgroup, parg = \
            self.generator._setUp(test_alignments, [None, None])
        self.assertEqual(alignment.get_alignment_length(),
                         test_alignment.get_alignment_length())
        self.assertEqual(carg, self.carg)
        self.assertTrue(outgroup in self.poutgroups)
        self.assertEqual(parg, self.parg)

    def test_generator_run(self):
        self.assertTrue(self.generator.run())

    @unittest.skipIf(not ptools.raxml, "Requires RAxML")
    def test_raxml(self):
        # write out a .constraint.tre
        with open('.constraint.tre', 'w') as file:
            Phylo.write(self.constraint, file, 'newick')
        # write out a .partitions.txt
        with open('.partitions.txt', 'w') as file:
            file.write(self.partition_text)
        phylo = self.true_RAxML(test_alignment, wd=self.wd, logger=self.logger,
                                threads=2, partitions=self.parg,
                                outgroup=self.poutgroups[0],
                                constraint=self.carg)
        self.assertTrue(phylo)

    def test_consensus(self):
        # create a list of trees and make a consensus
        phylogenies = [self.phylo for i in range(100)]
        ptools.consensus(phylogenies=phylogenies, outdir='.', min_freq=0.5,
                         is_rooted=True, trees_splits_encoded=False)
        self.assertTrue(os.path.isfile('consensus.tre'))

if __name__ == '__main__':
    unittest.main()
