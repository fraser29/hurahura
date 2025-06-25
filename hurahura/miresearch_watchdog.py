
import os
import time
import shutil
import uuid
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
#
from hurahura import mi_subject
from hurahura.mi_config import MIResearch_config


# ====================================================================================================
# ====================================================================================================
def getLogger(id, logfileName, DEBUG=False):
    logger = logging.getLogger(id)
    if DEBUG:
       logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    fh = logging.FileHandler(logfileName, encoding='utf-8')
    fh.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-7s | %(name)s | %(message)s', 
                                    datefmt='%d-%b-%y %H:%M:%S'))
    logger.addHandler(fh)
    logger.info(f'===== INIT {id} LOGGER ===== ')
    return logger

# ====================================================================================================
# ====================================================================================================
class MIResearch_WatchDog(object):
    """A watchdog for MI Research built off watchdog
    Will watch a directory and load new subjects as they arrive
    """
    def __init__(self, directoryToWatch, 
                 dataStorageRoot,
                 subjectPrefix,
                 SubjClass=mi_subject.AbstractSubject,
                 DEBUG=False) -> None:
        self.directoryToWatch = directoryToWatch
        self.dataStorageRoot = dataStorageRoot
        self.subjectPrefix = subjectPrefix
        self.SubjClass = SubjClass
        self.recursive = False
        self.DEBUG = DEBUG
        #
        self.processDir = os.path.join(self.directoryToWatch, 'MIResearch-PROCESSING')
        # self.completeDir = os.path.join(self.directoryToWatch, 'MIResearch-COMPLETE')
        self.errorDir = os.path.join(self.directoryToWatch, 'MIResearch-ERROR')
        os.makedirs(self.processDir, exist_ok=True)
        os.makedirs(self.errorDir, exist_ok=True)
        # os.makedirs(self.completeDir, exist_ok=True)
        # If storage dir not exist (but root directory does exist) then make
        if not os.path.isdir(self.dataStorageRoot): 
            if os.path.isdir(os.path.split(self.dataStorageRoot)[0]):
                os.makedirs(self.dataStorageRoot)
        #
        self.logger = getLogger(subjectPrefix, os.path.join(self.processDir, "mi_watcher.log"), self.DEBUG)
        # 
        self.event_handler = MIResearch_SubdirectoryHandler(self.directoryToWatch,
                                                            self.dataStorageRoot,
                                                            self.subjectPrefix,
                                                            self.logger,
                                                            self.SubjClass,
                                                            self.DEBUG)
        self.event_handler.processDir = self.processDir
        self.event_handler.errorDir = self.errorDir
        # self.event_handler.completeDir = self.completeDir


    def run(self):    
        observer = Observer()
        observer.schedule(self.event_handler, path=self.directoryToWatch, recursive=self.recursive)
        self.logger.info(f"Starting MIResearch_WatchDog")
        self.logger.info(f" watching: {self.directoryToWatch}")
        self.logger.info(f" storage destination: {self.dataStorageRoot}")
        self.logger.info(f" subject prefix: {self.subjectPrefix}")
        self.logger.info(f" SubjectClass: {self.SubjClass}")
        self.logger.debug(f" RUNNING IN DEBUG MODE")
        observer.start()
        self.logger.info(f" -------------- OBSERVER STARTED --------------")
        try:
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            self.logger.info(f"MIResearch_WatchDog watching {self.directoryToWatch} killed.")
            self.logger.info("Closing cleanly. ")
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
                 logger,
                 SubjClass=mi_subject.AbstractSubject,
                 DEBUG=False) -> None:
        super(MIResearch_SubdirectoryHandler, self).__init__()
        self.directoryToWatch = directoryToWatch
        self.dataStorageRoot = dataStorageRoot
        self.subjectPrefix = subjectPrefix
        self.logger = logger
        self.SubjClass = SubjClass
        self.DEBUG = DEBUG
        #
        self.ignore_pattern = ['.WORKING', 'MIResearch-']
        # Polling
        self.pollDelay = 5 # seconds
        self.pollStable = max([MIResearch_config.stable_directory_age_sec, self.pollDelay+1])
        self.pollTimeOut = 10*self.pollStable
        # NOTE:
        # self.processDir and self.errorDir are set on the FileSystemEventHandler by the MIResearch_WatchDog class

    def on_moved(self, event):
        if event.is_directory:
            self.logger.info(f"Directory moved/renamed: {event.dest_path}")
            try:
                self._action(event.dest_path)
            except Exception as e:
                self.logger.error(f"    _action processing interrupted : {e}")

    def on_created(self, event):
        if event.is_directory:
            self.logger.info(f"Directory created: {event.src_path}")
            try:
                self._action(event.src_path)
            except Exception as e:
                self.logger.error(f"    _action processing interrupted : {e}")

        elif event.src_path.endswith('.zip') or \
                event.src_path.endswith('.tar') or \
                event.src_path.endswith('.tar.gz'):
            self.logger.info(f"Archive created: {event.src_path}") # Note other archives are not handled
            try:
                self._action(event.src_path)
            except Exception as e:
                if self.DEBUG:
                    raise e
                self.logger.error(f"    _action processing interrupted : {e}")
        
        elif event.src_path.endswith('kill_watcher'):
            os.unlink(event.src_path)
            raise KeyboardInterrupt

    def on_deleted(self, event):
        self.logger.info(f"deleted: {event.src_path}")
        pass
    # def on_modified(self, event):
    #     pass

    def _action(self, new_subdirectory_full):
        self.logger.info(f"New subdirectory detected: {new_subdirectory_full}")
        subdirectory = os.path.split(new_subdirectory_full)[1]

        if self.ignore_pattern and self.matches_ignore_pattern(subdirectory):
            self.logger.info(f"Ignoring subdirectory: {new_subdirectory_full}")
            return

        if self.is_stable(new_subdirectory_full):
            self.logger.info(f"STABLE: {new_subdirectory_full}")
            # Want to process a directory - but if already being processed then need to deal with that first. 
            matchingProcessing = self.findMatchingProcessingDirs(subdirectory)
            if len(matchingProcessing) > 0:
                for already_exec_directory in matchingProcessing:
                    self.logger.warning(f"Found already executing directory: {already_exec_directory}")
                    self.logger.warning(f"DELETING {already_exec_directory}")
                    try: 
                        shutil.rmtree(already_exec_directory)
                    except NotADirectoryError: # MAY BE A zip or tar file
                        os.unlink(already_exec_directory)
                    except FileNotFoundError:
                        self.logger.error(f"Error: Directory '{already_exec_directory}' does not exist - maybe just finished.")
                    except Exception as e:
                        self.logger.error(f"An error occurred: {e}")
            ## 
            self.execute_loadDirectory(new_subdirectory_full)


    def findMatchingProcessingDirs(self, src_path):
        matchingProcessing = []
        self.logger.debug(f"DEBUG: check {self.processDir} for matching {src_path}")
        for iDir in os.listdir(self.processDir):
            if src_path in iDir:
                matchingProcessing.append(os.path.join(self.processDir, iDir))
        return matchingProcessing

    def is_stable(self, directory_path):
        """Check if this new directory is stable (no change in modified time)

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
            if (current_time - start_time) > (self.pollTimeOut): 
                break
            if stable_start_time is None:
                # Initialize stable_start_time on the first iteration
                stable_start_time = current_time
            modified_time = get_directory_modified_time(directory_path)
            if modified_time > stable_start_time: 
                stable_start_time = modified_time
            if current_time - stable_start_time >= self.pollStable:
                self.logger.debug(f"Directory has remained stable for {self.pollStable} seconds.")
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
        uid = uuid.uuid4().hex
        src_path = os.path.split(directoryToLoad)[1]
        directoryToLoad_process = shutil.move(directoryToLoad, os.path.join(self.processDir, uid+"_"+src_path))
        try:
            self.logger.info(f"*** BEGIN PROCESSING {directoryToLoad_process} ***")
            newSubjList = mi_subject.createNew_OrAddTo_Subject(directoryToLoad_process,
                                                dataRoot=self.dataStorageRoot,
                                                SubjClass=self.SubjClass,
                                                subjPrefix=self.subjectPrefix,
                                                OTHER_DATA_DIR=directoryToLoad_process)

        except Exception as e:
            self.logger.error(f"An error occurred while loading subject: {str(e)} ")
            if self.DEBUG:
                raise e
            else:
                # Move the directory to the error directory
                finalCompleteDir = os.path.join(self.errorDir, os.path.split(directoryToLoad_process)[1])
                if os.path.isdir(finalCompleteDir):
                    self.logger.warning(f"{finalCompleteDir} exists - will delete before moving {directoryToLoad_process}")
                    shutil.rmtree(finalCompleteDir)
                shutil.move(directoryToLoad_process, self.errorDir)
                self.logger.error(f"An error occurred while loading subject: {str(e)} data moved to {self.errorDir}")
                return
        self.logger.info(f"   FINISHED LOADING {directoryToLoad_process} ===")
        try:
            shutil.rmtree(directoryToLoad_process)
            self.logger.info(f"   DELETED {directoryToLoad_process} ===")
        except NotADirectoryError: # MAY BE A zip or tar file
            os.unlink(directoryToLoad_process) 
            self.logger.info(f"   DELETED {directoryToLoad_process} ===")
        except Exception as e:
            self.logger.error(f"An error occurred while deleting {directoryToLoad_process}: {str(e)}")

        self.logger.info(f"=== FINISHED PROCESSING {directoryToLoad_process} ===")


### ====================================================================================================================
class MIResearchWatchDogError(Exception):
    """A custom error class."""

    def __init__(self, message="An error occurred"):
        super().__init__(message)
        self.message = message