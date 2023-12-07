# -*- coding: utf-8 -*-

"""Module that exposes the routines and utilities making up MIRESEARCH
"""

import os
import sys
import argparse

from miresearch import mi_utils
from miresearch import mi_subject



def buildNewSubject(dataRoot, SubjectClass, dicomDirectory=None):
    """Will build a new subject of SubjectClass in dataRoot using dicomDirectory to populate 

    Args:
        dataRoot (str): path to root directory of subject filesystem database
        SubjectClass (mi_subject.AbstractSubject): class mi_subject.AbstractSubject (or derived from)
        dicomDirectory (str, optional): Path to directory of dicoms to load into new subject. Defaults to None.
    """
    newSubj = SubjectClass()


def buildNewSubject_Multi(dataRoot, directoryOfDicomStudies, subjectPrefix=None):
    if subjectPrefix is None:
        subjectPrefix = mi_subject.guessSubjectPrefix(dataRoot)


def seeWhatIveGotIn_kmr():
    pass



### ====================================================================================================================
##          RUN VIA MAIN
### ====================================================================================================================
# Override error to show help on argparse error (missing required argument etc)
class MiResearchParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

def setNList(args):
    if len(args.subjRange) == 2:
        args.subjNList = args.subjNList+list(range(args.subjRange[0], args.subjRange[1]))
    if args.subjNListFile:
        args.subjNList = args.subjNList+mi_utils.subjFileToSubjN(args.subjNListFile)
    # args.subjNList = sorted(list(set(args.subjNList)))


def checkArgs(args):
    if args.dataRoot is not None:
        args.dataRoot = os.path.abspath(args.dataRoot)
    else:
        args.dataRoot = mi_utils.getDataRoot()
    if not args.QUIET:
        print(f'Running MIRESEARCH with dataRoot {args.dataRoot}')
    if args.loadPath is not None:
        args.loadPath = os.path.abspath(args.loadPath)
        if not args.QUIET:
            print(f'Running MIRESEARCH with loadPath {args.loadPath}')
    ## -------------
    setNList(args=args)

##  ========= RUN ACTIONS =========
def runActions(args):
    if args.loadPath is not None:
        mi_subject.createNewSubjectHelper(args.loadPath)
    ####
        ##

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
    ParentAP = MiResearchParser(add_help=False,
                                epilog='Fraser M. Callaghan', 
                                description='Medical Imaging Research assistant - miresearch')
    
    groupS = ParentAP.add_argument_group('Subject Definition')
    groupS.add_argument('-s', dest='subjNList', help='Subject number', nargs="*", type=int, default=[])
    groupS.add_argument('-sf', dest='subjNListFile', help='Subject numbers in file', type=str, default=None)
    groupS.add_argument('-sR', dest='subjRange', help='Subject range', nargs=2, type=int, default=[])
    groupS.add_argument('-y', dest='dataRoot', help='Path of root data directory (where subjects are stored) [dfault None -> will get from config file]', type=str, default=None)
    groupS.add_argument('-load', dest='loadPath', help='Path to load dicoms from (file / directory / tar / tar.gz / zip)', type=str, default=None)
    groupS.add_argument('-LoadMulti', dest='LoadMulti', help='Load new subject for each subdirectory under loadPath', action='store_true')


    groupS.add_argument('-FORCE', dest='FORCE', help='force reading even if not standard dicom (needed if dicom files missing header meta)',
                            action='store_true')
    groupS.add_argument('-QUIET', dest='QUIET', help='Suppress progress bars and logging to terminal',
                            action='store_true')
    ##
    arguments = ParentAP.parse_args()
    checkArgs(arguments)
    return arguments


if __name__ == '__main__':
    main()