#! /bin/usr/env python
# D.J. Bennett
# 26/05/2014
"""
Test alignment stage.
"""

import unittest
import pickle
import os
import shutil
from pglt.stages import alignment_stage
from Bio import AlignIO
from pglt.tools.alignment_tools import mafft

# DIRS
working_dir = os.path.dirname(__file__)


# DUMMIES
class Dummy_SeqStore(object):
    def __init__(self, gene_dir, seq_files, minfails, mingaps, minoverlap,
                 logger, wd):
        pass

    def __len__(self):
        return 0

    def keys(self):
        return []  # acts like a dictionary


class Dummy_Aligner(object):
    def __init__(self, seqstore, mingaps, minoverlap, minseedsize,
                 maxseedsize, maxtrys, maxseedtrys, gene_type, outgroup,
                 logger, wd):
        pass

    def run(self):
        return alignment

# TEST DATA
# reference alignment
with open(os.path.join(working_dir, 'data',
          'test_alignment_ref.faa'), 'r') as file:
    alignment = AlignIO.read(file, 'fasta')

# reference genedict
genedict = {'rbcl': {'mingaps': 0.1, 'minoverlap': 0.1, 'maxtrys': 100,
                     'minseedsize': 5, 'maxseedsize': 20, 'maxseedtrys': 10,
                     'minfails': 10, 'type': 'both'},
            'COI': {'mingaps': 0.1, 'minoverlap': 0.1, 'maxtrys': 100,
                    'minseedsize': 5, 'maxseedsize': 20, 'maxseedtrys': 10,
                    'minfails': 10, 'type': 'shallow'}}

# reference paradict
paradict = {'naligns': 1}  # don't let it run more than once

# reference namesdict
namesdict = {}  # all the names in reference alignment
names = ['Ignatius_tetrasporus', 'Oltmannsiellopsis_viridis',
         'Scotinosphaera_austriaca_H5304', 'Scotinosphaera_facciolae_H5309',
         'Scotinosphaera_gibberosa_H5301', 'Scotinosphaera_gibberosa_H5302',
         'Scotinosphaera_lemnae_H5303a', 'Scotinosphaera_lemnae_H5303b',
         'Scotinosphaera_sp_H5305', 'Scotinosphaera_sp_H5306',
         'Ulothrix_zonata']
for name in names:
    namesdict[name] = {"txids": [1, 2], "unique_name": name, "rank": 'species',
                       'genes': 2}


@unittest.skipIf(not mafft, "Requires MAFFT")
class AlignmentStageTestSuite(unittest.TestCase):

    def setUp(self):
        # stub functions and class
        self.True_SeqStore = alignment_stage.atools.SeqStore
        self.True_Aligner = alignment_stage.atools.Aligner
        alignment_stage.atools.SeqStore = Dummy_SeqStore
        alignment_stage.atools.Aligner = Dummy_Aligner
        # write out necessary files to run
        os.mkdir('tempfiles')
        with open(os.path.join('tempfiles', "genedict.p"), "wb") as file:
            pickle.dump(genedict, file)
        with open(os.path.join('tempfiles', "paradict.p"), "wb") as file:
            pickle.dump(paradict, file)
        with open(os.path.join('tempfiles', "namesdict.p"), "wb") as file:
            pickle.dump(namesdict, file)
        # download files so it can 'read' in sequences
        os.mkdir('2_download')
        os.mkdir(os.path.join('2_download', 'COI'))
        os.mkdir(os.path.join('2_download', 'rbcl'))

    def tearDown(self):
        # remove all files and folders potentially generated by alignment stage
        alignment_folders = ['2_download', '3_alignment', 'tempfiles']
        while alignment_folders:
            try:
                alignment_folder = alignment_folders.pop()
                shutil.rmtree(alignment_folder)
            except OSError:
                pass
        alignment_stage.atools.SeqStore = self.True_SeqStore
        alignment_stage.atools.Aligner = self.True_Aligner

    def test_alignment_stage(self):
        # run
        res = alignment_stage.run()
        self.assertIsNone(res)

if __name__ == '__main__':
    unittest.main()
