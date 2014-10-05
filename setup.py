#! /usr/bin/env python
## D.J. Bennett
## 26/05/2014
"""
Setup.py for mpe
"""
import os,subprocess,re,sys
from setuptools import setup, find_packages

## Functions
def getVersion(args):
	"""Return version number of program"""
	# check if program exists
	try:
		# run, read and kill
		process = subprocess.Popen(args, stdout = subprocess.PIPE,
			stderr=subprocess.STDOUT)
		info = process.stdout.read()
		process.kill()
		# find version number, extract and strip of digits
		pattern = '(v|version)?\s?[0-9]\.[0-9]+'
		res = re.search(pattern, info)
		version = info[res.span()[0]:res.span()[1]]
		non_decimal = re.compile(r'[^\d.]+')
		version = non_decimal.sub('', version)
		return float(version)
	except OSError:
		return False

def read(fname):
	return open(os.path.join(os.path.dirname(__file__), fname)).read()

## Check external programs
# '-u' prevents printing to shell
all_present = True
if not getVersion(['mafft', '-u']):
	print 'No MAFFT detected -- requires MAFFT v7+'
	all_present = False
if getVersion(['mafft', '-u']) < 7.0:
	print 'MAFFT detected too old -- requires MAFFT v7+'
if not getVersion(['mafft-xinsi', '-u']):
	print 'No mafft-xinsi detected -- requires installation of\
 mafft with RNA structural alignments'
	all_present = False
if not getVersion(['mafft-qinsi', '-u']):
	print 'No mafft-qinsi detected -- requires installation of\
 mafft with RNA structural alignments'
	all_present = False
if getVersion(['raxml', '-version']) < 7.0:
	print 'No RAxML detected -- requires RAxML v7+'
	all_present = False
if getVersion(['blastn', '-h']) < 2.0:
	print 'No Stand-alone BLAST detected -- requires BLAST suite v2+'
	all_present = False
if not all_present:
	sys.exit('Unable to install/test! Please install missing external programs')

## Package info
PACKAGES = find_packages()
PACKAGE_DIRS = [p.replace(".", os.path.sep) for p in PACKAGES]

## Setup
setup(
	name = "mpe",
	version = "1.0.0",
	author = "Dominic John Bennett",
	author_email = "dominic.john.bennett@gmail.com",
	description = ("An automated pipeline for phylogeney generation."),
	license = "LICENSE.txt",
	keywords = "ecology evolution conservation phylogenetics",
	url = "https://github.com/DomBennett/MassPhylogenyEstimation",
	packages = PACKAGES,
	package_dir = dict(zip (PACKAGES, PACKAGE_DIRS)),
	package_data = {'mpe':['parameters.csv','gene_parameters.csv']},
	scripts = ['run_mpe.py'],
	test_suite = 'tests',
	long_description = read('README.md'),
	classifiers=[
		"Development Status :: 1 - Planning",
		"Topic :: Scientific/Engineering :: Bio-Informatics",
		"Programming Language :: Python :: 2.7",
		"License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
	],
	install_requires=[
		  # -*- Extra requirements: -*-
		  'setuptools',
		  'taxon_names_resolver',
		  'biopython',
		  'dendropy',
		  'numpy',
		  'scipy',
	  ],
)