
from context import miresearch # This is useful for testing outside of environment

import os
import unittest
import shutil
from miresearch import mi_subject
from miresearch import config


this_dir = os.path.split(os.path.realpath(__file__))[0]
DCM_DIRECTORY = os.path.join(this_dir, 'TEST_DATA')
dcm001 = os.path.join(DCM_DIRECTORY, 'IM-00041-00001.dcm')
TEMP_DIRECTORY = os.path.join(this_dir, 'LOAD_DIR')


class TestSubject(unittest.TestCase):
    def runTest(self):
        newSubj = mi_subject.AbstractSubject('MI000001', TEMP_DIRECTORY)
        newSubj.loadDicomsToSubject(DCM_DIRECTORY)
        self.assertEqual(newSubj.countNumberOfDicoms(), 2, msg="Incorrect number of dicoms")
        newSubj.buildSeriesDataMetaCSV()
        newSubj.studyDicomTagsToMeta()
        pWeight = int(newSubj.getTagValue('PatientWeight'))
        self.assertEqual(pWeight, 80, msg="Got incorrect tag - weight")
        self.assertEqual(newSubj.getTagValue('StudyDate'), "20140409", msg="Got incorrect tag - studydate")
        dcmStr = newSubj.getDicomFoldersListStr()
        print(dcmStr)

        if not config.DEBUG:
            shutil.rmtree(TEMP_DIRECTORY)
        


if __name__ == '__main__':
    unittest.main()
