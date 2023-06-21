
from context import miresearch # This is useful for testing outside of environment

import os
import unittest
import shutil
from miresearch import mi_subject


this_dir = os.path.split(os.path.realpath(__file__))[0]
DCM_DIRECTORY = os.path.join(this_dir, 'TEST_DATA')
dcm001 = os.path.join(DCM_DIRECTORY, 'IM-00041-00001.dcm')
TEMP_DIRECTORY = os.path.join(this_dir, 'LOAD_DIR')
DEBUG = False


class TestSubject(unittest.TestCase):
    def runTest(self):
        newSubj = mi_subject.AbstractSubject('MI000001', TEMP_DIRECTORY)
        newSubj.loadDicomsToSubject(DCM_DIRECTORY)
        # if not DEBUG:
        #     shutil.rmtree(tmpDir)
        


if __name__ == '__main__':
    unittest.main()
