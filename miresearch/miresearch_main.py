# -*- coding: utf-8 -*-

"""Module that exposes the routines and utilities making up MIRESEARCH
"""

import os
import sys

from miresearch import mi_utils
from miresearch import mi_subject
from miresearch import miresearch_watchdog
from miresearch.mi_config import MIResearch_config


### ====================================================================================================================
##          RUN VIA MAIN
### ====================================================================================================================
def checkArgs(args):
    # 
    MIResearch_config.runconfigParser(args.configFile)
    if args.INFO:
        MIResearch_config.printInfo()
        sys.exit(1)
    #
    if args.dataRoot is not None:
        args.dataRoot = os.path.abspath(args.dataRoot)
    else:
        args.dataRoot = mi_utils.getDataRoot()
    if not args.QUIET:
        print(f'Running MIRESEARCH with dataRoot {args.dataRoot}')
    if args.loadPath is not None:
        args.loadPath = os.path.abspath(args.loadPath)
    if args.LoadMultiForce:
        args.LoadMulti = True
    ## -------------
    mi_utils.setNList(args=args)

##  ========= RUN ACTIONS =========
def runActions(args):
    if args.loadPath is not None:
        if len(args.subjNList) == 0:
            args.subjNList = [None]
        if not args.QUIET:
            print(f'Running MIRESEARCH with loadPath {args.loadPath}')
        mi_subject.createNew_OrAddTo_Subject(loadDirectory=args.loadPath,
                                             dataRoot=args.dataRoot,
                                             subjPrefix=args.subjPrefix,
                                             subjNumber=args.subjNList[0],
                                             anonName=args.anonName,
                                             LOAD_MULTI=args.LoadMulti,
                                             IGNORE_UIDS=args.LoadMultiForce,
                                             QUIET=args.QUIET)
    elif args.anonName is not None:
        for sn in args.subjNList:
            iSubj = mi_subject.AbstractSubject(sn, args.dataRoot, args.subjPrefix)
            iSubj.anonymise(args.anonName)

    elif args.SummaryCSV is not None:
        mi_subject.WriteSubjectStudySummary(args.dataRoot, args.SummaryCSV)
    
    ## WATCH DIRECTORY ##
    elif args.WatchDirectory is not None:

        MIWatcher = miresearch_watchdog.MIResearch_WatchDog(args.WatchDirectory,
                                        args.dataRoot,
                                        args.subjPrefix,
                                        TO_ANONYMISE=(args.anonName is not None))

### ====================================================================================================================
### ====================================================================================================================
# S T A R T
def main():
    arguments = parseArgs(sys.argv[1:])
    runActions(arguments)

def parseArgs(args):
    # --------------------------------------------------------------------------
    #  ARGUMENT PARSING
    # --------------------------------------------------------------------------
    ParentAP = mi_utils.MiResearchParser(parents=[mi_utils.ParentAP, mi_utils.SubjectInput], 
                                description='Medical Imaging Research assistant - miresearch')
    
    groupA = ParentAP.add_argument_group('Actions')
    groupA.add_argument('-Load', dest='loadPath', 
                        help='Path to load dicoms from (file / directory / tar / tar.gz / zip)', 
                        type=str, default=None)
    groupA.add_argument('-LOAD_MULTI', dest='LoadMulti', 
                        help='Combine with "Load": Load new subject for each subdirectory under loadPath', 
                        action='store_true')
    groupA.add_argument('-LOAD_MULTI_FORCE', dest='LoadMultiForce', 
                        help='Combine with "Load": Force to ignore studyUIDs and load new ID per subdirectory', 
                        action='store_true')
    groupA.add_argument('-WatchDirectory', dest='WatchDirectory', 
                        help='Will watch given directory for new data and load as new study', 
                        type=str, default=None)
    groupA.add_argument('-SummaryCSV', dest='SummaryCSV', 
                        help='Write summary CSV file (give output file name)', 
                        type=str, default=None)

    ##
    arguments = ParentAP.parse_args(args)
    checkArgs(arguments)
    return arguments


if __name__ == '__main__':
    main()