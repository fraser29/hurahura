# -*- coding: utf-8 -*-

"""Module that exposes the routines and utilities making up MIRESEARCH
"""

import os
import sys

from miresearch import mi_utils
from miresearch import mi_subject
from miresearch import miresearch_watchdog
from miresearch.mi_config import MIResearch_config


# ### ====================================================================================================================
# ##          RUN VIA MAIN
# ### ====================================================================================================================
##  ========= CHECK ARGS =========
def checkArgs(args):
    # 
    if args.configFile: MIResearch_config.runconfigParser(args.configFile)
    if args.INFO:
        MIResearch_config.printInfo()
        sys.exit(1)
    #
    if args.dataRoot is not None:
        args.dataRoot = os.path.abspath(args.dataRoot)
    else:
        args.dataRoot = MIResearch_config.data_root_dir
    if args.subjPrefix is None:
        args.subjPrefix = MIResearch_config.subject_prefix
    if args.anonName is None:
        args.anonName = MIResearch_config.anon_level
    if not args.QUIET:
        print(f'Running MIRESEARCH with dataRoot {args.dataRoot}')
    if args.loadPath is not None:
        args.loadPath = os.path.abspath(args.loadPath)
    if args.LoadMultiForce:
        args.LoadMulti = True
    
    MISubjClass = mi_subject.AbstractSubject
    if MIResearch_config.class_obj:
        MISubjClass = MIResearch_config.class_obj
    args.MISubjClass = MISubjClass
    ## -------------
    mi_utils.setNList(args=args)

# ##  ========= RUN ACTIONS =========
def runActions(args, extra_runActions=None):

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
                                             SubjClass=args.MISubjClass,
                                             IGNORE_UIDS=args.LoadMultiForce,
                                             QUIET=args.QUIET)
    # SUBJECT LEVEL actions
    elif len(args.subjNList) > 0:
        # ANONYMISE
        if args.anonName is not None:
            for sn in args.subjNList:
                iSubj = args.MISubjClass(sn, args.dataRoot, args.subjPrefix)
                iSubj.anonymise(args.anonName)

        elif args.subjRunPost:
            for sn in args.subjNList:
                iSubj = args.MISubjClass(sn, args.dataRoot, args.subjPrefix)
                iSubj.runPostLoadPipeLine()

        elif args.subjInfo:
            for sn in args.subjNList:
                iSubj = args.MISubjClass(sn, args.dataRoot, args.subjPrefix)
                iSubj.info()

    # SUBJECT GROUP (based on dataRoot) ACTIONS
    elif args.SummaryCSV is not None:
        mi_subject.WriteSubjectStudySummary(args.dataRoot, args.SummaryCSV)
    


    ## WATCH DIRECTORY ##
    elif args.WatchDirectory is not None:

        MIWatcher = miresearch_watchdog.MIResearch_WatchDog(args.WatchDirectory,
                                        args.dataRoot,
                                        args.subjPrefix,
                                        SubjClass=args.MISubjClass,
                                        TO_ANONYMISE=(args.anonName is not None))
        MIWatcher.run()

    if extra_runActions is not None:
        extra_runActions(args)

### ====================================================================================================================
### ====================================================================================================================
# S T A R T
def main(extra_runActions=None):
    arguments = mi_utils.ParentAP.parse_args()
    checkArgs(arguments) # Will substitute from config files if can
    runActions(arguments, extra_runActions)


if __name__ == '__main__':
    main()