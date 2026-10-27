.. _usage_subclass:

Usage_subclass
===============

---------------------------------------------------------
*Subclassing AbstractSubject*
---------------------------------------------------------

To really take advantage of hurahura subclassing the primary classes is recommended. 

When subclassing a user has access to all functionality of hurahura with all typical tasks of data loading, anonymization, generating summaries, querying etc implemented already. The user may therefore focus on generating their own pipelines and analysis. 

The template below is heavily commented to show how customization may be performed. 

.. code-block:: python

    # Template for subclassing AbstractSubject

    # Import miresearch_main and mi_subject from hurahura
    # miresearch_main is the main function that handles the dispatching of actions to the correct class. 
    # mi_subject is the AbstractSubject class that is sub-classed to create the subject object. 
    from hurahura import miresearch_main, mi_subject

    # MIResearch_config provides access to the config file. 
    from hurahura.mi_config import MIResearch_config # Provides access to the config file parameters

    class MySubject(mi_subject.AbstractSubject):
        def __init__(self, subjectNumber, 
                            dataRoot=MIResearch_config.data_root_dir,
                            subjectPrefix=MIResearch_config.subject_prefix,
                            suffix="") -> None:
            AbstractSubject.__init__(self, subjectNumber=subjectNumber,
                                                dataRoot=dataRoot,
                                                subjectPrefix=subjectPrefix,
                                                suffix=suffix)
            """
            Subject number is the ID (int) of the subject of interest. 
            dataRoot is the directory where all your SUBJ0000ID subjects are stored.
            subjectPrefix is the short prefix ( "SUBJ" in the example above ) 
            suffix is provided for flexibility but is NOT RECOMMENDED to be used. 

            dataRoot and subjectPrefix have default values picked up from your active config file
            but these may also be overwritten at the commandline. 
            """

            # Some standard information is defined by the *.conf file
            #
            # example use of customised conf file parameters:
            self.path_to_my_atlas = MIResearch_config.params['parameters'].get("example_path_to_atlas", None)
            # see how this is used in runMyAutomaticSegmentationPipeline() below


        ### ----------------------------------------------------------------------------------------------------------------
        ### Overriding methods
        ### ----------------------------------------------------------------------------------------------------------------
        def runPostLoadPipeLine(self):
            """
            Example overriding method to run a post load pipeline
            This is run after any new subject is loaded. 
            It can also be run at any time from the command line via 
            MyProject -s N -RunPost
                this will run runPostLoadPipeLine() on subject number N
            """
            self.logger.info(f"Running post load pipeline for {self.subjID}")

            # Enter post load pipeline steps here
            # e.g.
            result = self.runMyAutomaticSegmentationPipeline() # See example below
            if result == 0: 
                self.printVolumeInfo()
                

        ## Example customised pipeline for your data
        def runMyAutomaticSegmentationPipeline(self, FORCE=False):
            segmentationOutputFile = self.getSegmentationOutputFile()
            if not FORCE and os.path.isfile(segmentationOutputFile):
                return 0
            if (self.path_to_my_atlas is None) or (not os.path.isfile(self.path_to_my_atlas)): 
                self.logger.error("Can not run segmentation - atlas not given")
                return 1
            try:
                import fancy_MIT_registration_module
                myFetalBrainDicomsDirectory = self.findDicomSeries("SeriesDescription_FetalBrain")
                fancy_MIT_registration_module(myFetalBrainDicomsDirectory, 
                                            outputFile=segmentationOutputFile, 
                                            atlasFile=self.path_to_my_atlas)
            except ImportError:
                self.logger.error("Could not import fancy_MIT_registration_module ")
                return 1
            except:
                self.logger.error("Error running MIT segmentation code")
                return 1


        def calculateWhiteMatterVolume(self):
            segFile = self.getSegmentationOutputFile()
            if os.path.isfile(segFile):
                return 42  # it is possible some more fancy calculation is required here - this is just an example
            return 0.0


        def printVolumeInfo(self):
            vol = self.calculateWhiteMatterVolume()
            print(f"{self.subjID} is {self.getAge()} years old and has a white matter volume of {vol:0.2f} (via MIT atlas method)")


        def getSegmentationOutputFile(self):
            return os.path.join(self.getSegmentationDir(), f"{self.subjID}_Segmentation_MITAtlas.nii")

        ### ----------------------------------------------------------------------------------------------------------------
        ### Directory paths
        ### ----------------------------------------------------------------------------------------------------------------
        def getSegmentationDir(self):
            return self._getDir(["SEGMENTATION"])



    ### ====================================================================================================================
    #      THIS IS HOW TO CUSTOMISE COMMAND LINE ACTIONS
    ### ====================================================================================================================
    def getArgGroup():
        groupMyProject = miresearch_main.ParentAP.add_argument_group('MyProject Actions')
        # EXAMPLES - CHANGE BELOW
        groupMyProject.add_argument('-vol', dest='runVolumeAction', help='Run my pipeline specific to these subjects', action='store_true')
        groupMyProject.add_argument('-findMatchingExams', dest='findMatchingExams', help='Find matching exams for the given subject (use e.g. -sA to query against all subjects)', type=int, default=[])
        #
        return groupMyProject
        ##


    def MyProject_specific_actions(args):
        """
        This is an example of how to customise the command line actions.
        """
        if args.runVolumeAction: 
            # Here we build a list of subjects as we go
            for sn in args.subjNList:
                iSubj = MIResearch_config.class_obj(sn, MIResearch_config.data_root_dir, MIResearch_config.subject_prefix)
                if iSubj.exists():
                    iSubj.printVolumeInfo()


    ### ====================================================================================================================
    ### ====================================================================================================================

    def main():
        getArgGroup()
        ##
        # Note that any MyProject_specific actions along with the class object are passed to the main function. 
        # We let the miresearch_main function handle the dispatching of actions to the correct class. 
        miresearch_main.main(extra_runActions=[MyProject_specific_actions], class_obj=MyProjectSubject)


    # S T A R T
    if __name__ == '__main__':
        main()



