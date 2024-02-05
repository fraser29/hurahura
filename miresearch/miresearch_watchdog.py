
import os
import sys
import time
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

    def run(self):    
        observer = Observer()
        observer.schedule(self.event_handler, path=self.directoryToWatch, recursive=self.recursive)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()


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
        self.ignore_pattern = '.WORKING'
        # Polling
        self.pollDelay = 5 # seconds
        self.pollStable = max([MIResearch_config.stable_directory_age_sec, self.pollDelay+1])
        self.pollTimeOut = 10*self.pollStable

    def on_created(self, event):
        if event.is_directory:
            new_subdirectory = os.path.join(self.parent_directory, event.src_path)

            if self.ignore_pattern and self.matches_ignore_pattern(new_subdirectory):
                print(f"Ignoring subdirectory: {new_subdirectory}")
                return

            if self.is_stable(new_subdirectory):
                print(f"New subdirectory detected: {new_subdirectory}")
                self.execute_loadDirectory(new_subdirectory)

    def on_deleted(self, event):
        if event.is_directory:
            pass

    def is_stable(self, directory_path):
        start_time = time.time()
        stable_start_time = None

        while True:
            current_time = time.time()
            # Check if the timeout has been reached
            if current_time - start_time > self.pollTimeOut:
                print(f"Timeout reached ({self.pollTimeOut} seconds). Returning True.")
                return True
            # Check the modified time of the directory
            modified_time = os.path.getmtime(directory_path)
            if stable_start_time is None:
                # Initialize stable_start_time on the first iteration
                stable_start_time = current_time
            elif current_time - stable_start_time >= self.pollStable:
                print(f"Directory has remained stable for {self.pollStable} seconds.")
                return True
            time.sleep(self.pollDelay)
        return False

    def matches_ignore_pattern(self, subdirectory):
        # Check if the subdirectory matches the ignore pattern
        return self.ignore_pattern in subdirectory

    def execute_loadDirectory(self, directoryToLoad):
        # TODO: move to a .WORKING directory. Move to a COMPLETE directory (COMPLETE as an ignore rule. )
        newSubjList = mi_subject.createNew_OrAddTo_Subject(directoryToLoad,
                                             dataRoot=self.dataStorageRoot,
                                             SubjClass=self.SubjClass,
                                             subjPrefix=self.subjectPrefix)
        if self.TO_ANONYMISE:
            for iNewSubj in newSubjList:
                iNewSubj.anonymise()


### ====================================================================================================================