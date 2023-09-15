
from context import miresearch # This is useful for testing outside of environment

import os
import unittest
import shutil
from miresearch import mi_subject
from miresearch import config


this_dir = os.path.split(os.path.realpath(__file__))[0]
TEST_DIR = os.path.join(this_dir, 'TEST_DATA')
P1 = os.path.join(TEST_DIR, 'P1')
P2 = os.path.join(TEST_DIR, 'P2')
P3_4 = os.path.join(TEST_DIR, "P3_4")
P4_extra = os.path.join(TEST_DIR, "P4_extra")


class TestSubject(unittest.TestCase):
    def setUp(self):
        self.tmpDir = os.path.join(this_dir, 'tmpTestSubj')
        # print(f"Building {self.tmpDir}")
        if os.path.isdir(self.tmpDir):
            self.tearDown()
        os.makedirs(self.tmpDir)
        self.newSubj = mi_subject.AbstractSubject('MI000001', self.tmpDir)
        self.newSubj.QUIET = True
        self.newSubj.loadDicomsToSubject(P1, HIDE_PROGRESSBAR=True)

    def test_newSubj(self):
        self.assertEqual(self.newSubj.countNumberOfDicoms(), 2, msg="Incorrect number of dicoms")

        self.newSubj.buildSeriesDataMetaCSV()
        self.assertTrue(os.path.isfile(self.newSubj.getSeriesMetaCSV()))

        self.newSubj.buildDicomMeta()
        self.assertTrue(os.path.isfile(self.newSubj.getMetaTagsFile()))

        pWeight = int(self.newSubj.getTagValue('PatientWeight'))
        self.assertEqual(pWeight, 80, msg="Got incorrect tag - weight")
        self.assertEqual(self.newSubj.getTagValue('StudyDate'), "20140409", msg="Got incorrect tag - studydate")

        nSE_dict = self.newSubj.getSeriesNumbersMatchingDescriptionStr('RVLA')
        self.assertEqual(int(list(nSE_dict.keys())[0]), 41, msg="Error finding se matching SeriesDescription")

    def tearDown(self):
        shutil.rmtree(self.tmpDir)

class TestSubjects(unittest.TestCase):
    def setUp(self):
        self.tmpDir = os.path.join(this_dir, 'tmpTestSubjs')
        # print(f"Building {self.tmpDir}")
        if os.path.isdir(self.tmpDir):
            self.tearDown()
        os.makedirs(self.tmpDir)
        self.newSubj = mi_subject.AbstractSubject('MI000001', self.tmpDir)
        self.newSubj.QUIET = True
        self.newSubj.loadDicomsToSubject(P1, HIDE_PROGRESSBAR=True)
        self.newSubj = mi_subject.AbstractSubject('MI000002', self.tmpDir)
        self.newSubj.QUIET = True
        self.newSubj.loadDicomsToSubject(P2, HIDE_PROGRESSBAR=True)
        self.newSubj.buildDicomMeta()
        self.newSubj = mi_subject.AbstractSubject('MI000003', self.tmpDir)
        self.newSubj.QUIET = True
        self.newSubj.loadDicomsToSubject(P3_4, HIDE_PROGRESSBAR=True)
        self.subjList = mi_subject.SubjectList.setByDirectory(self.tmpDir)

    def test_newSubjs(self):
        self.assertTrue(os.path.isdir(os.path.join(self.tmpDir, 'MI000001')))
    
    def test_List(self):
        self.assertEqual(len(self.subjList), 3, "Error making subject list")
        
    def test_filterList(self):
        filtList = self.subjList.filterSubjectListByDOS('20111014')
        self.assertEqual(len(filtList), 1, "Error filtering subject list")
        

    def tearDown(self):
        shutil.rmtree(self.tmpDir)
        

        

if __name__ == '__main__':
    # print(f"Running miresearch tests (DEBUG={config.DEBUG})")
    unittest.main(verbosity=2)
