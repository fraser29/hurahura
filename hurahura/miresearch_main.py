# -*- coding: utf-8 -*-

"""Module that exposes the routines and utilities making up MIRESEARCH
"""

import os
import sys
import argparse
import subprocess

from hurahura import mi_utils
from hurahura import mi_subject
from hurahura import miresearch_watchdog
from hurahura.mi_config import MIResearch_config


### ====================================================================================================================
#          ARGUEMTENT PARSING AND ACTIONS 
### ====================================================================================================================
# Override error to show help on argparse error (missing required argument etc)
class MiResearchParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

ParentAP = MiResearchParser(epilog="Written Fraser M. Callaghan. MRZentrum, University Children's Hospital Zurich")

groupM = ParentAP.add_argument_group('Management Parameters')
groupM.add_argument('-config', dest='configFile', help='Path to configuration file to use.', type=str, default=None)
groupM.add_argument('-FORCE', dest='FORCE', help='force action - use with caution',
                        action='store_true')
groupM.add_argument('-QUIET', dest='QUIET', help='Suppress progress bars and logging to terminal',
                        action='store_true')
groupM.add_argument('-INFO', dest='INFO', help='Provide setup (configuration) info and exit.',
                        action='store_true')
groupM.add_argument('-DEBUG', dest='DEBUG', help='Run in DEBUG mode (save intermediate steps, increase log output)',
                        action='store_true')

groupS = ParentAP.add_argument_group('Subject Definition')
groupS.add_argument('-s', dest='subjNList', help='Subject number(s)', nargs="*", type=int, default=[])
groupS.add_argument('-sA', dest='AllSubjs', help='All subjects', action='store_true')
groupS.add_argument('-sf', dest='subjNListFile', help='Subject numbers in file', type=str, default=None)
groupS.add_argument('-sR', dest='subjRange', help='Subject range', nargs=2, type=int, default=[])
groupS.add_argument('-y', dest='dataRoot', 
                    help='Path of root data directory (where subjects are stored) [default None -> may be set in config file]', 
                    type=str, default=None)
groupS.add_argument('-sPrefix', dest='subjPrefix', 
                    help='Subject prefix [default None -> will get from config file OR dataRoot]', 
                    type=str, default=None)
groupS.add_argument('-sSuffix', dest='subjSuffix', 
                    help='Subject suffix [default ""]', 
                    type=str, default="")
groupS.add_argument('-anonName', dest='anonName', 
                    help='Set to anonymise newly loaded subject. Set to true to use for WatchDirectory. [default None]', 
                    type=str, default=None)
    
## === ACTIONS ===
groupA = ParentAP.add_argument_group('Actions')
groupA.add_argument('-Build', dest='build', 
                    help='Build empty subject(s)', 
                    action='store_true')
# LOADING
groupA.add_argument('-Load', dest='loadPath', 
                    help='Path to load data from (file / directory / tar / tar.gz / zip)', 
                    type=str, default=None)
groupA.add_argument('-LoadOther', dest='loadPathOther', 
                    help='Path to load other data from directory (non-DICOM)', 
                    type=str, default=None)
groupA.add_argument('-LOAD_MULTI', dest='LoadMulti', 
                    help='Combine with "Load": Load new subject for each subdirectory under loadPath', 
                    action='store_true')
groupA.add_argument('-LOAD_MULTI_FORCE', dest='LoadMultiForce', 
                    help='Combine with "Load": Force to ignore studyUIDs and load new ID per subdirectory', 
                    action='store_true')

# SUBJECT LEVEL
groupA.add_argument('-RunPost', dest='subjRunPost', 
                    help='Run post load pipeline', 
                    action='store_true')
groupA.add_argument('-SubjInfo', dest='subjInfo', 
                    help='Print info for each subject', 
                    action='store_true')
groupA.add_argument('-SubjInfoFull', dest='subjInfoFull', 
                    help='Print full info for each subject', 
                    action='store_true')

# GROUP ACTIONS
groupA.add_argument('-SummaryCSV', dest='SummaryCSV', 
                    help='Write summary CSV file (give output file name)', 
                    type=str, nargs="*", default=None)
groupA.add_argument('-Summary', dest='Summary', 
                    help='Print summary of provided subjects to commandline (best with -sA option)', 
                    action='store_true')

# WATCH DIRECTORY
groupA.add_argument('-WatchDirectory', dest='WatchDirectory', 
                    help='Will watch given directory for new data and load as new study', 
                    type=str, default=None)

# UI STUFF
# groupA.add_argument('-UI', dest='UI', 
#                     help='Run in UI mode', 
#                     action='store_true')
# groupA.add_argument('-UI_port', dest='UI_port', 
#                     help='Port to run UI on', 
#                     type=int, default=8080)

## === QUERY ===
groupQ = ParentAP.add_argument_group('Query')
groupQ.add_argument('-qSeriesDesc', dest='qSeriesDesc', 
                    help='Query based on a series description (must provide -s* option)', 
                    type=str, default=None)
groupQ.add_argument('-qPID', dest='qPID', 
                    help='Query based on patient ID (must provide -s* option)', 
                    type=str, default=None)
groupQ.add_argument('-qPatName', dest='qPatName', 
                    help='Query based on a patient name (must provide -s* option)', 
                    type=str, default=None)
groupQ.add_argument('-qExamID', dest='qExamID', 
                    help='Query based on exam (scanner assigned) ID (must provide -s* option)', 
                    type=str, default=None)
groupQ.add_argument('-qDate', dest='qDate', 
                    help='Query based on study date: provide start and end, YYYYMMDD (must provide -s* option)', 
                    type=str, default=[], nargs=2)

### ====================================================================================================================
#           CHECK ARGS
### ====================================================================================================================

def setNList(args):
    if args.AllSubjs:
        args.subjNList = mi_subject.getAllSubjectsN(args.dataRoot, args.subjPrefix)
    else:
        if len(args.subjRange) == 2:
            args.subjNList = args.subjNList+list(range(args.subjRange[0], args.subjRange[1]))
        if args.subjNListFile:
            args.subjNList = args.subjNList+mi_utils.subjFileToSubjN(args.subjNListFile)
    # args.subjNList = sorted(list(set(args.subjNList)))

def checkArgs(args, class_obj=None):
    # 
    args.RUN_ANON = False
    if args.configFile: MIResearch_config.runConfigParser(args.configFile)
    #
    if args.dataRoot is not None:
        args.dataRoot = os.path.abspath(args.dataRoot)
    else:
        args.dataRoot = MIResearch_config.data_root_dir
    if args.subjPrefix is None:
        args.subjPrefix = MIResearch_config.subject_prefix
    if args.anonName is None:
        args.anonName = MIResearch_config.anon_level
    else: 
        args.RUN_ANON = True
    if not args.QUIET:
        print(f'Running MIRESEARCH with dataRoot {args.dataRoot}')
    if args.loadPath is not None:
        args.loadPath = os.path.abspath(args.loadPath)
    if args.LoadMultiForce:
        args.LoadMulti = True
    
    MISubjClass = mi_subject.AbstractSubject
    if class_obj is not None:
        if isinstance(class_obj, str):
            class_obj = mi_subject.get_configured_subject_class(class_obj)
        else:
            MIResearch_config.class_obj = class_obj
    if MIResearch_config.class_obj:
        if isinstance(MIResearch_config.class_obj, str):
            MIResearch_config.class_obj = mi_subject.get_configured_subject_class(MIResearch_config.class_obj)
        MISubjClass = MIResearch_config.class_obj
    args.MISubjClass = MISubjClass
    ## -------------
    if args.INFO:
        MIResearch_config.printInfo()
        sys.exit(1)
    setNList(args=args)

### ====================================================================================================================
#           RUN ACTIONS
### ====================================================================================================================
def runActions(args, extra_runActions=None):

    # --- LOAD ---
    if args.loadPath is not None:
        if len(args.subjNList) == 0:
            args.subjNList = [None]
        if not args.QUIET:
            print(f'Running MIRESEARCH with loadPath {args.loadPath}')
        subjList = mi_subject.createNew_OrAddTo_Subject(loadDirectory=args.loadPath,
                                             dataRoot=args.dataRoot,
                                             subjPrefix=args.subjPrefix,
                                             subjNumber=args.subjNList[0],
                                             anonName=args.anonName,
                                             LOAD_MULTI=args.LoadMulti,
                                             SubjClass=args.MISubjClass,
                                             IGNORE_UIDS=args.LoadMultiForce,
                                             OTHER_DATA_DIR=args.loadPathOther,
                                             QUIET=args.QUIET)
        args.subjNList = [iSubj.subjN for iSubj in subjList]

    # SPECIAL ACTION - BUILD EMPTY SUBJECT(S)
    elif args.build:
        subjList = mi_subject.SubjectList([args.MISubjClass(sn, args.dataRoot, args.subjPrefix, suffix=args.subjSuffix) for sn in args.subjNList])
        for iSubj in subjList:
            if not iSubj.exists():
                print(f"Building: {iSubj.subjID}...")
                iSubj.initDirectoryStructure()
        args.subjNList = [iSubj.subjN for iSubj in subjList]

    # ------------------------------------------------------------------------------------------------------------------------------
    # SUBJECT LEVEL actions
    if len(args.subjNList) > 0:
        if args.DEBUG:
            print(f"SubjList provided is: {args.subjNList}")
        subjList = mi_subject.SubjectList([args.MISubjClass(sn, args.dataRoot, args.subjPrefix, suffix=args.subjSuffix) for sn in args.subjNList])
        subjList.reduceToExist(args.DEBUG)

        if args.DEBUG:
            for iSubj in subjList:
                iSubj.setDEBUGMode(args.DEBUG)

        if args.loadPathOther is not None:
            if len(subjList) == 1:
                subjList[0].addOtherData(args.loadPathOther)
            else:
                print(f"Warning: -LoadOther option only supported for single subject")

        # --- QUERY ---
        if args.qSeriesDesc:
            for iSubj in subjList:
                if args.DEBUG:
                    print(f"Searching: {iSubj.subjID}...")
                res = iSubj.getSeriesNumbersMatchingDescriptionStr(args.qSeriesDesc)
                if len(res) > 0:
                    print(f"{iSubj} has {list(res.values())}")

        if args.qPID:
            subList = subjList.findSubjMatchingPatientID(args.qPID)
            for iSubj in subList:
                print(iSubj.info())

        if args.qPatName:
            subList = subjList.findSubjMatchingName(args.qPatName)
            for iSubj in subList:
                print(iSubj.info())

        if args.qExamID:
            subList = subjList.findSubjMatchingStudyID(args.qExamID)
            for iSubj in subList:
                print(iSubj.info())

        if len(args.qDate) == 2:
            subList = subjList.filterSubjectListByDOS(args.qDate[0], args.qDate[1])
            for iSubj in subList:
                print(iSubj.info())

        # --- ANONYMISE ---
        elif args.RUN_ANON:
            if args.anonName is not None:
                for iSubj in subjList:
                    if not args.QUIET:
                        print(f"Anonymise: {iSubj.subjID}...")
                    iSubj.anonymise(args.anonName)

        # --- POST LOAD PIPELINE ---
        elif args.subjRunPost:
            for iSubj in subjList:
                if not args.QUIET:
                    print(f"Post load pipeline: {iSubj.subjID}...")
                iSubj.runPostLoadPipeLine()

        # --- PRINT INFO ---
        elif args.subjInfo:
            HEADER = False
            for iSubj in subjList:
                data, header = iSubj.getInfoStr()
                if not HEADER:
                    print(",".join(header))
                    HEADER = True
                print(",".join([str(i) for i in data]))

        elif args.subjInfoFull:
            for iSubj in subjList:
                if args.DEBUG:
                    print(f"Info: {iSubj.subjID}...")
                iSubj.infoFull()
                    

        # === SUBJECT GROUP ACTIONS ===
        # --- SummaryCSV ---
        elif args.SummaryCSV is not None:
            if not args.QUIET:
                print(f"Info: writting summary for {len(args.subjNList)} subjects at {args.dataRoot} to {args.SummaryCSV[0]}")
                if len(args.SummaryCSV) > 1:
                    print(f"  With tags: {args.SummaryCSV[1:]}")
            subjList.writeSummaryCSV(args.SummaryCSV[0], extra_series_tags=args.SummaryCSV[1:])
        
        # --- Summary ---
        elif args.Summary:
            if not args.QUIET:
                print(f"Info: summary for {len(args.subjNList)} subjects at {args.dataRoot}")
            print(subjList)

    ## WATCH DIRECTORY ##
    elif args.WatchDirectory is not None:

        MIWatcher = miresearch_watchdog.MIResearch_WatchDog(args.WatchDirectory,
                                        args.dataRoot,
                                        args.subjPrefix,
                                        SubjClass=args.MISubjClass,
                                        DEBUG=args.DEBUG)
        MIWatcher.run()


    ## UI ##
    # elif args.UI:
    #     miresearchui_path = os.path.join(os.path.dirname(__file__), 'miresearchui')
    #     subprocess.Popen(['python', 'mainUI.py', str(args.UI_port)], cwd=miresearchui_path)

    if extra_runActions is not None:
        if type(extra_runActions) == list:
            for iExtra in extra_runActions:
                try:
                    iExtra(args)
                except AttributeError as AttrError:
                    print(f"Error in extra action {iExtra}: Has the configuration been set up correctly (esp. 'class_path')?")
                    raise AttrError
                except Exception as e:
                    print(f"Error: {e}") 
        else:
            try:
                extra_runActions(args)
            except Exception as e:
                print(f"Error: {e}") 

### ====================================================================================================================
### ====================================================================================================================
# S T A R T
def main(extra_runActions=None, class_obj=None):
    arguments = ParentAP.parse_args()
    checkArgs(arguments, class_obj) # Will substitute from config files if can
    runActions(arguments, extra_runActions)


if __name__ in {"__main__", "__mp_main__"}:
    main()