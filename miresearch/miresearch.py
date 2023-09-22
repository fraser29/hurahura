# -*- coding: utf-8 -*-

"""Module that exposes the routines and utilities making up MIRESEARCH
"""

import os
import sys
import argparse

# Local imports 
import miresearch.mi_subject as mi_subject


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
class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)


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
    ap = MyParser(description='Medical Imaging Research assistant - miresearch')

    ap.add_argument('-i', dest='inputPath', help='Path to find dicoms (file or directory or tar or tar.gz or zip)', type=str, required=True)
    ap.add_argument('-y', dest='dataRoot', help='Path for output - if set then will organise dicoms into this folder', type=str, default=None)

    ap.add_argument('-FORCE', dest='FORCE', help='force reading even if not standard dicom (needed if dicom files missing header meta)',
                            action='store_true')
    ap.add_argument('-QUIET', dest='QUIET', help='Suppress progress bars and information output to terminal',
                            action='store_true')
    ##

    arguments = ap.parse_args()
    if arguments.inputPath is not None:
        arguments.inputPath = os.path.abspath(arguments.inputPath)
        if not arguments.QUIET:
            print(f'Running SPYDCMTK with input {arguments.inputPath}')
    ## -------------

    runActions(arguments, ap)


if __name__ == '__main__':

    main()