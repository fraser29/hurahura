#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test abstraction of mi_subject
"""

import os

from hurahura import miresearch_main, mi_subject
from hurahura.mi_config import MIResearch_config



# ====================================================================================================
#       SUBJECT CLASS
# ====================================================================================================
class TESTSubject(mi_subject.AbstractSubject):
    def __init__(self, subjectNumber, 
                        dataRoot=MIResearch_config.data_root_dir,
                        subjectPrefix=MIResearch_config.subject_prefix,
                        suffix="") -> None:
        mi_subject.AbstractSubject.__init__(self, subjectNumber=subjectNumber,
                                            dataRoot=dataRoot,
                                            subjectPrefix=subjectPrefix,
                                            suffix=suffix)


    ### ----------------------------------------------------------------------------------------------------------------
    ### Overriding methods
    ### ----------------------------------------------------------------------------------------------------------------
    def runPostLoadPipeLine(self):
        self.logger.info(f"Running post load pipeline for {self.subjID}")



### ====================================================================================================================
#      THIS IS HOW TO CUSTOMISE COMMAND LINE ACTIONS
### ====================================================================================================================
def getArgGroup():
    groupTEST = miresearch_main.ParentAP.add_argument_group('TEST Actions')
    groupTEST.add_argument('-nothing', dest='nothing', help='Do nothing', action='store_true')
    return groupTEST
    ##


def TEST_specific_actions(args):
    """
    This is an example of how to customise the command line actions.
    """
    if args.nothing: 
        # Here we build a list of subjects as we go
        for sn in args.subjNList:
            iSubj = MIResearch_config.class_obj(sn, MIResearch_config.data_root_dir, MIResearch_config.subject_prefix)
            if iSubj.exists():
                iSubj.logger.info(f"Subject {iSubj.subjID} exists")


### ====================================================================================================================
### ====================================================================================================================

def main():
    getArgGroup() # This line adds your personalised arguments defined above
    #
    miresearch_main.main(extra_runActions=[TEST_specific_actions], class_obj=TESTSubject)

# S T A R T
if __name__ == '__main__':
    main()
