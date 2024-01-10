
from context import miresearch # This is useful for testing outside of environment

import os
import unittest
import shutil

from miresearch import mi_utils
from miresearch import mi_subject


this_dir = os.path.split(os.path.realpath(__file__))[0]
TEST_DIR = os.path.join(this_dir, 'TEST_DATA')
P1 = os.path.join(TEST_DIR, 'P1')
P2 = os.path.join(TEST_DIR, 'P2')
P3_4 = os.path.join(TEST_DIR, "P3_4")
P4_extra = os.path.join(TEST_DIR, "P4_extra")
PZip  = os.path.join(TEST_DIR, "P3_4.zip")
PTar  = os.path.join(TEST_DIR, "P3_4.tar")
PTarGZ  = os.path.join(TEST_DIR, "P3_4.tar.gz")
DEBUG = mi_utils.mi_config.DEBUG

class TestSubject(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpDir = os.path.join(this_dir, 'tmpTestSubj')
        if os.path.isdir(cls.tmpDir):
            cls.tearDownClass(True)
        os.makedirs(cls.tmpDir)
        cls.newSubj = mi_subject.AbstractSubject(1, subjectPrefix='MI', dataRoot=cls.tmpDir)
        cls.newSubj.QUIET = True
        cls.newSubj.loadDicomsToSubject(P1, HIDE_PROGRESSBAR=True)
        cls.newSubj.loadDicomsToSubject(P1, HIDE_PROGRESSBAR=True)

    def test_newSubj(self):
        self.assertEqual(self.newSubj.countNumberOfDicoms(), 2, msg="Incorrect number of dicoms")

        self.newSubj.buildSeriesDataMetaCSV()
        self.assertTrue(os.path.isfile(self.newSubj.getSeriesMetaCSV()))

        self.newSubj.buildDicomMeta()
        self.assertTrue(os.path.isfile(self.newSubj.getMetaTagsFile()))

        pWeight = int(self.newSubj.getMetaTagValue('PatientWeight'))
        self.assertEqual(pWeight, 80, msg="Got incorrect tag - weight")
        self.assertEqual(self.newSubj.getMetaTagValue('StudyDate'), "20140409", msg="Got incorrect tag - studydate")

        nSE_dict = self.newSubj.getSeriesNumbersMatchingDescriptionStr('RVLA')
        self.assertEqual(int(list(nSE_dict.keys())[0]), 41, msg="Error finding se matching SeriesDescription")

    @classmethod
    def tearDownClass(cls, OVERRIDE=False):
        if (not DEBUG) or OVERRIDE:
            shutil.rmtree(cls.tmpDir)

class TestSubject2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpDir = os.path.join(this_dir, 'tmpTestSubj2')
        if os.path.isdir(cls.tmpDir):
            cls.tearDownClass(True)
        os.makedirs(cls.tmpDir)
        cls.newSubj = mi_subject.createNew_OrAddTo_Subject(P1, cls.tmpDir, subjPrefix='MI2', QUIET=True)[0]
        cls.newSubj.anonymise()

    def test_newSubj(self):
        self.assertTrue(os.path.isdir(os.path.join(self.tmpDir, 'MI2000001')))
        self.assertEqual(self.newSubj.countNumberOfDicoms(), 2, msg="Incorrect number of dicoms")

        pWeight = int(self.newSubj.getTagValue('PatientWeight'))
        self.assertEqual(pWeight, 80, msg="Got incorrect tag - weight")
        self.assertEqual(self.newSubj.getTagValue('StudyDate'), "20140409", msg="Got incorrect tag - studydate")

    @classmethod
    def tearDownClass(cls, OVERRIDE=False):
        if (not DEBUG) or OVERRIDE:
            shutil.rmtree(cls.tmpDir)


class TestSubjects(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpDir = os.path.join(this_dir, 'tmpTestSubjs')
        if os.path.isdir(cls.tmpDir):
            cls.tearDownClass(True)
        os.makedirs(cls.tmpDir)
        cls.newSubj1 = mi_subject.AbstractSubject(1, subjectPrefix='MI', dataRoot=cls.tmpDir)
        cls.newSubj1.QUIET = True
        cls.newSubj1.loadDicomsToSubject(P1, HIDE_PROGRESSBAR=True)
        cls.newSubj2 = mi_subject.AbstractSubject(2, subjectPrefix='MI', dataRoot=cls.tmpDir)
        cls.newSubj2.QUIET = True
        cls.newSubj2.loadDicomsToSubject(P2, HIDE_PROGRESSBAR=True)
        cls.newSubj2.buildDicomMeta()
        cls.newSubj3 = mi_subject.AbstractSubject(3, subjectPrefix='MI', dataRoot=cls.tmpDir)
        cls.newSubj3.QUIET = True
        cls.newSubj3.loadDicomsToSubject(P3_4, HIDE_PROGRESSBAR=True)
        cls.subjList = mi_subject.SubjectList.setByDirectory(cls.tmpDir)

    def test_newSubjs(self):
        self.assertTrue(os.path.isdir(os.path.join(self.tmpDir, 'MI000001')))
    
    def test_List(self):
        self.assertEqual(len(self.subjList), 3, "Error making subject list")
        
    def test_filterList(self):
        filtList = self.subjList.filterSubjectListByDOS('20111014')
        self.assertEqual(len(filtList), 1, "Error filtering subject list")
        

    @classmethod
    def tearDownClass(cls, OVERRIDE=False):
        if (not DEBUG) or OVERRIDE:
            shutil.rmtree(cls.tmpDir)
        
class TestSubjects2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpDir = os.path.join(this_dir, 'tmpTestSubjs2')
        if os.path.isdir(cls.tmpDir):
            cls.tearDownClass(True)
        os.makedirs(cls.tmpDir)
        cls.subjList = mi_subject.createNew_OrAddTo_Subject(TEST_DIR, cls.tmpDir, subjPrefix='MI22', QUIET=True, LOAD_MULTI=True)

    def test_newSubjs(self):
        self.assertTrue(os.path.isdir(os.path.join(self.tmpDir, 'MI22000001')))
        self.assertTrue(os.path.isdir(os.path.join(self.tmpDir, 'MI22000002')))
        self.assertTrue(os.path.isdir(os.path.join(self.tmpDir, 'MI22000003')))
        self.assertFalse(os.path.isdir(os.path.join(self.tmpDir, 'MI22000004'))) # This false as "4" finds subject already exists and adds to 
    
    def test_List(self):
        self.assertEqual(len(self.subjList), 4, "Error making subject list")
        
    def test_filterList(self):
        filtList = self.subjList.filterSubjectListByDOS('20111014')
        self.assertEqual(len(filtList), 1, "Error filtering subject list")
        

    @classmethod
    def tearDownClass(cls, OVERRIDE=False):
        if (not DEBUG) or OVERRIDE:
            shutil.rmtree(cls.tmpDir)
                
class TestSubjects3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpDir = os.path.join(this_dir, 'tmpTestSubjs3')
        if os.path.isdir(cls.tmpDir):
            cls.tearDownClass(True)
        os.makedirs(cls.tmpDir)
        cls.subj = mi_subject.createNew_OrAddTo_Subject(TEST_DIR, cls.tmpDir, subjPrefix='MI3', anonName="SubjectNumber1", QUIET=True)[0]

    def test_newSubjs(self):
        self.assertTrue(os.path.isdir(os.path.join(self.tmpDir, 'MI3000001')))
    
    @classmethod
    def tearDownClass(cls, OVERRIDE=False):
        if (not DEBUG) or OVERRIDE:
            shutil.rmtree(cls.tmpDir)
        

# class TestMisc(unittest.TestCase):
#     def test_DefaultRootDir(self):
#         if DEBUG:
#             self.assertEqual(mi_utils.getDataRoot(), '"/Volume/MRI_DATA"', "Error Default DataRoot")
#         else:
#             self.assertEqual(mi_utils.getDataRoot(), "''", "Error Default DataRoot")
    
        
# class TestLoadCompressed(unittest.TestCase):

#     @classmethod
#     def setUpClass(cls):
#         cls.tmpDir = os.path.join(this_dir, 'tmpTestCompress')
#         if os.path.isdir(cls.tmpDir):
#             cls.tearDownClass(True)
#         os.makedirs(cls.tmpDir)
#         mi_subject.createNew_OrAddTo_Subject(PZip, cls.tmpDir, subjPrefix='MIZ', QUIET=True)
#         mi_subject.createNew_OrAddTo_Subject(PTar, cls.tmpDir, subjPrefix='MIT', QUIET=True)
#         cls.subjList = mi_subject.createNew_OrAddTo_Subject(PTarGZ, cls.tmpDir, subjPrefix='MITZ', QUIET=True, LOAD_MULTI=True)


#     def test_LoadZip(self):
#         self.assertTrue(os.path.isdir(os.path.join(self.tmpDir, 'MIZ000001')))
#         self.assertTrue(os.path.isdir(os.path.join(self.tmpDir, 'MIZ000002')))
#         dFile = self.subjList[1].getDicomFile(99, 1)
#         self.assertTrue(os.path.isfile(dFile), f'Not finding dcm file for {self.subjList[1].subjID}')

#     def test_LoadTar(self):
#         self.assertTrue(os.path.isdir(os.path.join(self.tmpDir, 'MIT000001')))
#         self.assertTrue(os.path.isdir(os.path.join(self.tmpDir, 'MIT000002')))

#     def test_LoadTarZ(self):
#         self.assertTrue(os.path.isdir(os.path.join(self.tmpDir, 'MITZ000001')))
#         self.assertTrue(os.path.isdir(os.path.join(self.tmpDir, 'MITZ000002')))

#     @classmethod
#     def tearDownClass(cls, OVERRIDE=False):
#         if (not DEBUG) or OVERRIDE:
#             shutil.rmtree(cls.tmpDir)
        

        

if __name__ == '__main__':
    print(f"Running miresearch tests (DEBUG={DEBUG})")
    unittest.main(verbosity=2)
