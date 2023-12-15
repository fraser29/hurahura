# -*- coding: utf-8 -*-

"""Module that exposes the routines and utilities making up MIRESEARCH
"""

import os
import sys

from miresearch import mi_utils
from miresearch import mi_subject
from miresearch import miresearch_watchdog


### ====================================================================================================================
##          RUN VIA MAIN
### ====================================================================================================================
def checkArgs(args):
    if args.dataRoot is not None:
        args.dataRoot = os.path.abspath(args.dataRoot)
    else:
        args.dataRoot = mi_utils.getDataRoot()
    if not args.QUIET:
        print(f'Running MIRESEARCH with dataRoot {args.dataRoot}')
    if args.loadPath is not None:
        args.loadPath = os.path.abspath(args.loadPath)
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
                                             QUIET=args.QUIET)
    ####
        ##
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
    ParentAP = mi_utils.MiResearchParser(epilog='Fraser M. Callaghan', 
                                description='Medical Imaging Research assistant - miresearch')
    
    groupS = ParentAP.add_argument_group('Subject Definition')
    groupS.add_argument('-s', dest='subjNList', help='Subject number', nargs="*", type=int, default=[])
    groupS.add_argument('-sf', dest='subjNListFile', help='Subject numbers in file', type=str, default=None)
    groupS.add_argument('-sR', dest='subjRange', help='Subject range', nargs=2, type=int, default=[])
    groupS.add_argument('-y', dest='dataRoot', 
                        help='Path of root data directory (where subjects are stored) [default None -> will get from config file]', 
                        type=str, default=None)
    groupS.add_argument('-sPrefix', dest='subjPrefix', 
                        help='Subject prefix [default None -> will get from config file]', 
                        type=str, default=None)
    groupS.add_argument('-anonName', dest='anonName', 
                        help='Set to anonymise newly loaded subject. Set to true to use for WatchDirectory. [default None]', 
                        type=str, default=None)

    groupA = ParentAP.add_argument_group('Actions')
    groupA.add_argument('-Load', dest='loadPath', 
                        help='Path to load dicoms from (file / directory / tar / tar.gz / zip)', 
                        type=str, default=None)
    groupA.add_argument('-LoadMulti', dest='LoadMulti', 
                        help='Load new subject for each subdirectory under loadPath', 
                        action='store_true')
    groupA.add_argument('-WatchDirectory', dest='WatchDirectory', 
                        help='Will watch given directory for new data and load as new study', 
                        type=str, default=None)


    groupM = ParentAP.add_argument_group('Management Parameters')
    groupM.add_argument('-FORCE', dest='FORCE', help='force action - use with caution',
                            action='store_true')
    groupM.add_argument('-QUIET', dest='QUIET', help='Suppress progress bars and logging to terminal',
                            action='store_true')
    ##
    arguments = ParentAP.parse_args(args)
    checkArgs(arguments)
    return arguments


if __name__ == '__main__':
    main()