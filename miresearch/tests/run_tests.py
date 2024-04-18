
from context import miresearch # This is useful for testing outside of environment

import os
import unittest
import shutil

from miresearch import mi_subject
from miresearch.mi_config import MIResearch_config


this_dir = os.path.split(os.path.realpath(__file__))[0]
TEST_DIR = os.path.join(this_dir, 'TEST_DATA', 'SINGLE')
P1 = os.path.join(TEST_DIR, 'P1')
P2 = os.path.join(TEST_DIR, 'P2')
P3 = os.path.join(TEST_DIR, "P3")
P4 = os.path.join(TEST_DIR, "P4")
P4_extra = os.path.join(TEST_DIR, "P4_extra")
PZip  = os.path.join(TEST_DIR, "P4.zip")
PTar  = os.path.join(TEST_DIR, "P3.tar")
PTarGZ  = os.path.join(TEST_DIR, "P4.tar.gz")
DEBUG = MIResearch_config.DEBUG

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
        # this forces a poor form of subjID - tests that subjN wrong later
        cls.newSubj = mi_subject.createNew_OrAddTo_Subject(P1, cls.tmpDir, subjPrefix='MI2', QUIET=True)[0]
        cls.newSubj.anonymise()

    def test_newSubj(self):
        self.assertTrue(os.path.isdir(os.path.join(self.tmpDir, 'MI2000001')))
        self.assertEqual(self.newSubj.countNumberOfDicoms(), 2, msg="Incorrect number of dicoms")

        pWeight = int(self.newSubj.getTagValue('PatientWeight'))
        self.assertEqual(pWeight, 80, msg="Got incorrect tag - weight")
        self.assertEqual(self.newSubj.getTagValue('StudyDate'), "20140409", msg="Got incorrect tag - studydate")
        self.assertNotEqual(self.newSubj.subjN, 1, msg="SubjN 1 is wrong")
        self.assertEqual(self.newSubj.subjN, 2000001, msg="SubjN 2000001 is wrong")

    @classmethod
    def tearDownClass(cls, OVERRIDE=False):
        if (not DEBUG) or OVERRIDE:
            shutil.rmtree(cls.tmpDir)


class TestSubject2b(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpDir = os.path.join(this_dir, 'tmpTestSubj2b')
        if os.path.isdir(cls.tmpDir):
            cls.tearDownClass(True)
        os.makedirs(cls.tmpDir)
        cls.newSubj1a = mi_subject.AbstractSubject(1, cls.tmpDir, 'OTHER', padZeros=3)
        cls.newSubj1b = mi_subject.AbstractSubject(1, cls.tmpDir, 'TMP', padZeros=6, suffix="_NN")
        cls.newSubj1a.loadDicomsToSubject(P1)
        cls.newSubj1b.loadDicomsToSubject(P1)
        # We add new subjet. Matching prefix (ignores suffix) auto increments number
        cls.newSubj2 = mi_subject.createNew_OrAddTo_Subject(P2, cls.tmpDir, subjPrefix='TMP')[0]

    def test_newSubj(self):
        self.assertTrue(os.path.isdir(os.path.join(self.tmpDir, 'OTHER001')))

    def test_N(self):
        self.assertEqual(self.newSubj1b.subjN, 1, msg="tmpTestSubj2b: 1 subjN is wrong")
        self.assertEqual(self.newSubj2.subjN, 2, msg="tmpTestSubj2b: 2 subjN is wrong")

    @classmethod
    def tearDownClass(cls, OVERRIDE=False):
        if (not DEBUG) or OVERRIDE:
            shutil.rmtree(cls.tmpDir)


class TestSubject3(unittest.TestCase): # No number in ID
    @classmethod
    def setUpClass(cls):
        cls.tmpDir = os.path.join(this_dir, 'tmpTestSubj3')
        if os.path.isdir(cls.tmpDir):
            cls.tearDownClass(True)
        os.makedirs(cls.tmpDir)
        cls.newSubj = mi_subject.createNew_OrAddTo_Subject(P1, cls.tmpDir, subjPrefix='MySpecialID', QUIET=True)[0]
        cls.newSubj.renameSubjID("MySpecialID")
        cls.newSubj.anonymise()

    def test_newSubj(self):
        self.assertTrue(os.path.isdir(os.path.join(self.tmpDir, 'MySpecialID')))
        self.assertEqual(self.newSubj.countNumberOfDicoms(), 2, msg="Incorrect number of dicoms")

        newSubjObj2 = mi_subject.AbstractSubject(subjectNumber="MySpecialID", dataRoot=self.tmpDir)

        pWeight = int(newSubjObj2.getTagValue('PatientWeight'))
        self.assertEqual(pWeight, 80, msg="Got incorrect tag - weight")
        self.assertEqual(newSubjObj2.getTagValue('StudyDate'), "20140409", msg="Got incorrect tag - studydate")

    @classmethod
    def tearDownClass(cls, OVERRIDE=False):
        if (not DEBUG) or OVERRIDE:
            shutil.rmtree(cls.tmpDir)


class TestSubject4(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpDir = os.path.join(this_dir, 'tmpTestSubj4')
        if os.path.isdir(cls.tmpDir):
            cls.tearDownClass(True)
        os.makedirs(cls.tmpDir)
        cls.newSubj = mi_subject.createNew_OrAddTo_Subject(P1, cls.tmpDir, subjPrefix='MIV', QUIET=True)[0]
        cls.newSubj.anonymise()

    def test_newSubj(self):
        self.assertTrue(os.path.isdir(os.path.join(self.tmpDir, 'MIV000001')))
        tStart, tEnd = self.newSubj.getStartTime_EndTimeOfExam()
        tTotal = self.newSubj.getTotalScanTime_s()
        self.assertEqual(tStart, 94627.4875)
        self.assertEqual(tEnd, '094627')
        self.assertEqual(tTotal, 0.0)
        self.assertEqual(self.newSubj.countNumberOfDicoms(), 2, msg="Incorrect number of dicoms")

        pWeight = int(self.newSubj.getTagValue('PatientWeight'))
        self.assertEqual(pWeight, 80, msg="Got incorrect tag - weight")
        self.assertEqual(self.newSubj.getTagValue('StudyDate'), "20140409", msg="Got incorrect tag - studydate")

    @classmethod
    def tearDownClass(cls, OVERRIDE=False):
        if (not DEBUG) or OVERRIDE:
            shutil.rmtree(cls.tmpDir)


class TestSubjectRename(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpDir = os.path.join(this_dir, 'tmpTestSubjRename')
        if os.path.isdir(cls.tmpDir):
            cls.tearDownClass(True)
        os.makedirs(cls.tmpDir)
        cls.newSubj = mi_subject.createNew_OrAddTo_Subject(P1, cls.tmpDir, subjPrefix='MIV', QUIET=True)[0]
        cls.newSubj.anonymise()

    def test_newSubj(self):
        self.assertTrue(os.path.isdir(os.path.join(self.tmpDir, 'MIV000001')))
        self.newSubj.renameSubjID("SUBJA_28.999.032")
        self.assertTrue(os.path.isdir(os.path.join(self.tmpDir, 'SUBJA_28.999.032')))

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
        cls.newSubj3.loadDicomsToSubject(P3, HIDE_PROGRESSBAR=True) # Can't do this as multiple subjects - how do i want to handle this
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
        cls.subjList = mi_subject.createNew_OrAddTo_Subject(TEST_DIR, cls.tmpDir, subjPrefix='MIBB', QUIET=True, LOAD_MULTI=True)

    def test_newSubjs(self):
        self.assertTrue(os.path.isdir(os.path.join(self.tmpDir, 'MIBB000001')))
        self.assertTrue(os.path.isdir(os.path.join(self.tmpDir, 'MIBB000002')))
        self.assertTrue(os.path.isdir(os.path.join(self.tmpDir, 'MIBB000003')))
        self.assertTrue(os.path.isdir(os.path.join(self.tmpDir, 'MIBB000004'))) # This false as "4" finds subject already exists and adds to 
    
    def test_List(self):
        self.assertEqual(len(self.subjList), 5, "Error making subject list")
        self.subjList.reduceToSet()
        self.assertEqual(len(self.subjList), 4, "Error making subject list after reduce")
        
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
        cls.subj = mi_subject.createNew_OrAddTo_Subject(P3, cls.tmpDir, subjPrefix='MIP', anonName="SubjectNumber1", QUIET=True)[0]

    def test_newSubjs(self):
        self.assertTrue(os.path.isdir(os.path.join(self.tmpDir, 'MIP000001')))
    
    @classmethod
    def tearDownClass(cls, OVERRIDE=False):
        if (not DEBUG) or OVERRIDE:
            shutil.rmtree(cls.tmpDir)
        
class TestArchiveSubject(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpDir = os.path.join(this_dir, 'tmpTestZip')
        if os.path.isdir(cls.tmpDir):
            cls.tearDownClass(True)
        os.makedirs(cls.tmpDir)
        cls.subj = mi_subject.createNew_OrAddTo_Subject(P4, cls.tmpDir, subjPrefix='MIZ', anonName="SubjectNumber1", QUIET=True)[0]

    def test_SubjZip(self):
        self.assertTrue(os.path.isdir(os.path.join(self.tmpDir, 'MIZ000001')))
        os.makedirs(os.path.join(self.tmpDir, 'ZIP'))
        os.makedirs(os.path.join(self.tmpDir, 'ZIP-onheRaw'))
        self.subj.zipUpSubject(os.path.join(self.tmpDir, 'ZIP'), EXCLUDE_RAW=False)
        self.subj.zipUpSubject(os.path.join(self.tmpDir, 'ZIP-onheRaw'), EXCLUDE_RAW=True)
    
    @classmethod
    def tearDownClass(cls, OVERRIDE=False):
        if (not DEBUG) or OVERRIDE:
            shutil.rmtree(cls.tmpDir)
                
class TestRenameSubject(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpDir = os.path.join(this_dir, 'tmpTestRename')
        if os.path.isdir(cls.tmpDir):
            cls.tearDownClass(True)
        os.makedirs(cls.tmpDir)
        cls.subj1 = mi_subject.createNew_OrAddTo_Subject(P3, cls.tmpDir, subjPrefix='MIZ', anonName="SubjectNumber1", QUIET=True)[0]
        cls.subj2 = mi_subject.createNew_OrAddTo_Subject(P4, cls.tmpDir, subjPrefix='MIZ', anonName="SubjectNumber2", QUIET=True)[0]

    def test_SubjRename(self):
        self.assertTrue(os.path.isdir(os.path.join(self.tmpDir, 'MIZ000001')))
        self.subj1.renameSubjID('Subject1')
        self.subj2.renameSubjID('Subject2')
        self.assertTrue(os.path.isdir(os.path.join(self.tmpDir, 'Subject2')))
        # self.subjList = mi_subject.SubjectList.setByDirectory(self.tmpDir)
        # print(self.subjList)
        # self.assertEqual(len(self.subjList), 2, "Error subject list wrong size")
        # sorted(self.subjList)




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
