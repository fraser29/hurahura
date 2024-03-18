
import os
import time
import shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
#
from miresearch import mi_subject
from miresearch.mi_config import MIResearch_config


class MIResearch_WatchDog(object):
    """A watchdog for MI Research built off watchdog
    Will watch a directory and load new subjects as they arrive
    """
    def __init__(self, directoryToWatch, 
                 dataStorageRoot,
                 subjectPrefix,
                 SubjClass=mi_subject.AbstractSubject,
                 TO_ANONYMISE=False) -> None:
        self.directoryToWatch = directoryToWatch
        self.dataStorageRoot = dataStorageRoot
        self.subjectPrefix = subjectPrefix
        self.SubjClass = SubjClass
        self.TO_ANONYMISE = TO_ANONYMISE
        self.recursive = False
        # 
        self.event_handler = MIResearch_SubdirectoryHandler(self.directoryToWatch,
                                                            self.dataStorageRoot,
                                                            self.subjectPrefix,
                                                            self.SubjClass,
                                                            self.TO_ANONYMISE)

    def buildWorkingDirectories(self):
        processDir = os.path.join(self.directoryToWatch, 'MIResearch-PROCESSING')
        completeDir = os.path.join(self.directoryToWatch, 'MIResearch-COMPLETE')
        os.makedirs(processDir, exist_ok=True)
        os.makedirs(completeDir, exist_ok=True)
        self.event_handler.processDir = processDir
        self.event_handler.completeDir = completeDir
        # If storage dir not exist (but root directory does exist) then make
        if not os.path.isdir(self.dataStorageRoot): 
            if os.path.isdir(os.path.split(self.dataStorageRoot)[0]):
                os.makedirs(self.dataStorageRoot)

    def run(self):    
        observer = Observer()
        observer.schedule(self.event_handler, path=self.directoryToWatch, recursive=self.recursive)
        print(f"\nStarting MIResearch_WatchDog")
        print(f"    watching: {self.directoryToWatch}")
        print(f"    storage destination: {self.dataStorageRoot}")
        print(f"    subject prefix: {self.subjectPrefix}")
        print(f"    anonymise: {self.TO_ANONYMISE}")
        print(f"    SubjectClass: {self.SubjClass}\n")
        self.buildWorkingDirectories()
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\nMIResearch_WatchDog watching {self.directoryToWatch} killed by keyborad interrupt.")
            print("Closing cleanly. ")
            observer.stop()
        observer.join()


def get_directory_modified_time(directory_path):
    modified_time = os.path.getmtime(directory_path)
    # Walk through the directory and its subdirectories
    for foldername, _, filenames in os.walk(directory_path):
        for filename in filenames:
            file_path = os.path.join(foldername, filename)
            file_modified_time = os.path.getmtime(file_path)
            modified_time = max(modified_time, file_modified_time)
    return modified_time

class MIResearch_SubdirectoryHandler(FileSystemEventHandler):
    def __init__(self, directoryToWatch, 
                 dataStorageRoot,
                 subjectPrefix,
                 SubjClass=mi_subject.AbstractSubject,
                 TO_ANONYMISE=False) -> None:
        super(MIResearch_SubdirectoryHandler, self).__init__()
        self.directoryToWatch = directoryToWatch
        self.dataStorageRoot = dataStorageRoot
        self.subjectPrefix = subjectPrefix
        self.SubjClass = SubjClass
        self.TO_ANONYMISE = TO_ANONYMISE
        #
        self.ignore_pattern = ['.WORKING', 'MIResearch-']
        # Polling
        self.pollDelay = 5 # seconds
        self.pollStable = max([MIResearch_config.stable_directory_age_sec, self.pollDelay+1])
        self.pollTimeOut = 10*self.pollStable

    def on_created(self, event):
        if event.is_directory:
            new_subdirectory = os.path.join(self.directoryToWatch, event.src_path)

            if self.ignore_pattern and self.matches_ignore_pattern(event.src_path):
                print(f"Ignoring subdirectory: {new_subdirectory}")
                return

            if self.is_stable(new_subdirectory):
                print(f"New subdirectory detected: {new_subdirectory}")
                self.execute_loadDirectory(new_subdirectory)

    def on_deleted(self, event):
        if event.is_directory:
            pass

    def is_stable(self, directory_path):
        """Check if this new directory is stable (no change in modified time)
        and is not already being processed - if hit timeout and still being processed then
        throw erro as something went wrong and will go wrong again. 

        Args:
            directory_path (str): the directory to check for stability

        Returns:
            bool: True if stable AND not already being processed. 
        """
        start_time = time.time()
        stable_start_time = None

        while True:
            current_time = time.time()
            # Check if the timeout has been reached
            if (current_time - start_time) > (self.pollTimeOut): # TODO do i want this???
                if os.path.isdir(os.path.join(self.processDir, os.path.split(directory_path)[1])):
                    print(f"Timeout reached ({self.pollTimeOut} seconds). Raising error as exists in {self.processDir}.")
                    raise MIResearchWatchDogError(f"Trying to process {directory_path}\nBut already being processed and timeout reached")
                else:
                    return True
            if stable_start_time is None:
                # Initialize stable_start_time on the first iteration
                stable_start_time = current_time
            modified_time = get_directory_modified_time(directory_path)
            if modified_time > stable_start_time: stable_start_time = modified_time
            if current_time - stable_start_time >= self.pollStable:
                # Now check if being processed
                if os.path.isdir(os.path.join(self.processDir, os.path.split(directory_path)[1])):
                    print(f"Directory stable but exists in {self.processDir}. Will wait.")    
                else:
                    print(f"Directory has remained stable for {self.pollStable} seconds.")
                    return True
            time.sleep(self.pollDelay)
        return False

    def matches_ignore_pattern(self, subdirectory):
        # Check if the subdirectory matches the ignore pattern
        for i in self.ignore_pattern:
            if i in subdirectory:
                return True
        return False

    def execute_loadDirectory(self, directoryToLoad):
        directoryToLoad_process = shutil.move(directoryToLoad, self.processDir)
        newSubjList = mi_subject.createNew_OrAddTo_Subject(directoryToLoad_process,
                                             dataRoot=self.dataStorageRoot,
                                             SubjClass=self.SubjClass,
                                             subjPrefix=self.subjectPrefix)
        if self.TO_ANONYMISE:
            for iNewSubj in newSubjList:
                iNewSubj.anonymise()
        finalCompleteDir = os.path.join(self.completeDir, os.path.split(directoryToLoad_process)[1])
        if os.path.isdir(finalCompleteDir):
            print(f"{finalCompleteDir} exists - will delete befor moving {directoryToLoad_process}")
            shutil.rmtree(finalCompleteDir)
        shutil.move(directoryToLoad_process, self.completeDir)


### ====================================================================================================================
class MIResearchWatchDogError(Exception):
    """A custom error class."""

    def __init__(self, message="An error occurred"):
        super().__init__(message)
        self.message = message