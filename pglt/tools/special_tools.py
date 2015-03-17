#! /bin/usr/env python
# D.J. Bennett
# 06/11/2014
"""
pglt special tools
"""

# PACKAGES
import re
import os
import time
import sys
import subprocess
import shutil
import pickle
from tabulate import tabulate


# FUNCTIONS
def timeit(func, **kwargs):
    """Time a function (platform independent)"""
    # http://stackoverflow.com/questions/10884751/python-timeit-and-program-output
    if sys.platform == "win32":
        # On Windows, the best timer is time.clock()
        default_timer = time.clock
    else:
        # On most other platforms the best timer is time.time()
        default_timer = time.time
    t0 = default_timer()
    output = func(**kwargs)
    t1 = default_timer()
    return output, t1-t0


def getThreads(wd=None):
    """Find number of cores on machine (platform independent). If wd, \
search wd for pickled threads.p."""
    if wd:
        filepath = os.path.join(wd, 'threads.p')
        if os.path.isfile(filepath):
            with open(filepath, "rb") as file:
                nthreads = pickle.load(file)
        else:
            nthreads = 1
        return nthreads
    if sys.platform == 'darwin':
        # find threads for a mac
        cmd = "system_profiler SPHardwareDataType | grep Cores | awk \
'{print $5}'"
    elif sys.platform == 'linux2':
        # find threads for a unix
        cmd = "cat /proc/cpuinfo | grep processor | tail -1 | awk '{print $3}'"
    else:
        # TODO: work out n cores for windows
        # TODO: add a threads parameter to parameters.csv
        return 1
    s = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         shell=True)
    nthreads = s.stdout.readline()
    try:
        nthreads = int(nthreads)
    except:
        nthreads = 1
    return nthreads


def clean():
    """Remove all pglt files and folders"""
    # remove log.txt in parent folder
    try:
        os.remove('log.txt')
    except OSError:
        pass

    # remove tempfiles
    try:
        shutil.rmtree('tempfiles')
    except OSError:
        pass

    # remove resolved_names
    try:
        shutil.rmtree('resolved_names')
    except OSError:
        pass

    # go through all subdirs and remove files in list
    files_to_remove = ['info.txt', 'log.txt']
    folders = os.listdir(os.getcwd())
    while folders:
        temp_folder = folders.pop()
        temp_files_to_remove = files_to_remove[:]
        while temp_files_to_remove:
            temp_file_to_remove = temp_files_to_remove.pop()
            try:
                os.remove(os.path.join(temp_folder, temp_file_to_remove))
            except OSError:
                pass

    # go through all subdirs and remove folders in list
    folders_to_remove = ['1_names', '2_download', '3_alignment', '4_phylogeny',
                         'tempfiles']
    folders = os.listdir(os.getcwd())
    while folders:
        temp_folder = folders.pop()
        temp_folders_to_remove = folders_to_remove[:]
        while temp_folders_to_remove:
            temp_folder_to_remove = temp_folders_to_remove.pop()
            try:
                shutil.rmtree(os.path.join(temp_folder, temp_folder_to_remove))
            except OSError:
                pass


def reset(stage):
    """Reset progress dict"""
    folders = os.listdir(os.getcwd())
    for folder in folders:
        print (folder)
        progress_path = os.path.join(folder, 'tempfiles', 'progress.p')
        # if tempfiles exist, read in progress.p, delete stage folders
        if not os.path.isfile(progress_path):
            print('here')
            continue
        with open(progress_path, "rb") as file:
            progress = pickle.load(file)
        stages = range(int(stage), 5)
        for s in stages:
            print(s)
            if s == 1:
                stage_folder = os.path.join(folder, '1_names')
                if os.path.isdir(stage_folder):
                    shutil.rmtree(stage_folder)
            if s == 2:
                stage_folder = os.path.join(folder, '2_download')
                if os.path.isdir(stage_folder):
                    shutil.rmtree(stage_folder)
            if s == 3:
                stage_folder = os.path.join(folder, '3_alignment')
                if os.path.isdir(stage_folder):
                    shutil.rmtree(stage_folder)
            if s == 4:
                stage_folder = os.path.join(folder, '4_phylogeny')
                if os.path.isdir(stage_folder):
                    shutil.rmtree(stage_folder)
            progress[str(s)] = 'not run'
        with open(progress_path, "wb") as file:
            progress = pickle.dump(progress, file)


def check(stage, stagecounter, directory):
        '''Check stage'''
        progress_path = os.path.join(directory, 'tempfiles', 'progress.p')
        if not os.path.isfile(progress_path):
            stagecounter[stage]['not run'] += 1
        else:
            with open(progress_path, "rb") as file:
                progress = pickle.load(file)
            stagecounter[stage][progress[stage]] += 1
        return stagecounter


def stats():
    """Print success status of folders"""
    # counter dicts
    statecounter = {'not run': 0, 'failed': 0, 'success': 0}
    stagecounter = {'1': statecounter.copy(), '2': statecounter.copy(),
                    '3': statecounter.copy(), '4': statecounter.copy()}
    consensus_counter = 0
    # get all folders
    folders = os.listdir(os.getcwd())
    avoid_pattern = "^\.|^log\.txt$|resolved_names|README|tempfiles"
    folders = [e for e in folders if not re.search(avoid_pattern, e)]
    stages = ['1', '2', '3', '4']
    for folder in folders:
        for stage in stages:
            stagecounter = check(stage=stage, stagecounter=stagecounter,
                                 directory=os.path.join(os.getcwd(), folder))
        if os.path.isfile(os.path.join(os.getcwd(), folder, '4_phylogeny',
                                       'consensus.tre')):
            consensus_counter += 1
    print ('\n{0}/{1} folders with phylogenetic trees....\n'.
           format(consensus_counter, len(folders)))
    headers = ['Stage', 'Not run', 'Failed', 'Success']
    rows = []
    for stage in stages:
        sc = stagecounter[stage]
        rows.append([stage, sc['not run'], sc['failed'], sc['success']])
    print(tabulate(rows, headers, tablefmt="simple"))
