# -*- coding: utf-8 -*-

"""Module that exposes the routines and utilities making up MIRESEARCH
"""

import os
import sys
import argparse

# Local imports 
import miresearch.mi_utils as mi_utils


def buildNewSubject(dbRoot, dicomDirectory=None, subjectSuffix=None):
    pass


def buildNewSubject_Multi(dbRoot, directoryOfDicomStudies, subjectSuffix=None):
    pass


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
    return True

##  ========= RUN ACTIONS =========
def runActions(args, ap):
    pass
    ####
        ##

### ====================================================================================================================
### ====================================================================================================================
# S T A R T
def main():
    # --------------------------------------------------------------------------
    #  ARGUMENT PARSING
    # --------------------------------------------------------------------------
    ParentAP = MiResearchParser(add_help=False,
                                       epilog='Fraser M. Callaghan', 
                                       description='Medical Imaging Research assistant - miresearch')
    
    groupS = ParentAP.add_argument_group('Subject Definition')
    groupS.add_argument('-i', dest='inputPath', help='Path to find dicoms (file / directory / tar / tar.gz / zip)', type=str, required=True)
    groupS.add_argument('-s', dest='subjNList', help='Subject number', nargs="*", type=int, default=[])
    groupS.add_argument('-sf', dest='subjNListFile', help='Subject numbers in file', type=str, default=None)
    groupS.add_argument('-sR', dest='subjRange', help='Subject range', nargs=2, type=int, default=[])
    groupS.add_argument('-y', dest='dataRoot', help='Path for output - if set then will organise dicoms into this folder', type=str, default=None)


    groupS.add_argument('-FORCE', dest='FORCE', help='force reading even if not standard dicom (needed if dicom files missing header meta)',
                            action='store_true')
    groupS.add_argument('-QUIET', dest='QUIET', help='Suppress progress bars and logging to terminal',
                            action='store_true')
    ##






    arguments = ParentAP.parse_args()
    if arguments.inputPath is not None:
        arguments.inputPath = os.path.abspath(arguments.inputPath)
        if not arguments.QUIET:
            print(f'Running MIRESEARCH with input {arguments.inputPath}')
    ## -------------

    runActions(arguments, ParentAP)


if __name__ == '__main__':

    main()