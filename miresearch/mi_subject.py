#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 26 10:59:36 2018

@author: Fraser M Callaghan

Classes for building standardised imaging projects. 
Adapted for general use from KMR project. 


"""


import os
import shutil
import numpy as np
import datetime
import pandas as pd
import logging
##
from spydcmtk import spydcm
from miresearch import mi_utils

abcList = 'abcdefghijklmnopqrstuvwxyz'

class DirectoryStructure(object):
    def __init__(self, name, childrenList=[]) -> None:
        super().__init__()
        self.name = name
        self.childrenList = childrenList

class DirectoryStructureTree():
    def __init__(self, topList) -> None:
        self.topList = topList


UNKNOWN = 'UNKNOWN'
META = "META"
RAW = "RAW"
DICOM = "DICOM"

DEFAULT_DIRECTORY_STRUCTURE_TREE = DirectoryStructureTree([DirectoryStructure('RAW', [DirectoryStructure('DICOM')]),
                                                            DirectoryStructure('META')])

# ====================================================================================================
#       ABSTRACT SUBJECT CLASS
# ====================================================================================================
class AbstractSubject(object):
    """
    An abstract subject controlling most basic structure
    """
    def __init__(self, subjectFullID, 
                        projectRoot, 
                        DIRECTORY_STRUCTURE_TREE=DEFAULT_DIRECTORY_STRUCTURE_TREE) -> None:
        self.subjID = subjectFullID
        self.dataRoot = projectRoot
        self.DIRECTORY_STRUCTURE_TREE = DIRECTORY_STRUCTURE_TREE
        self.BUILD_DIR_IF_NEED = True
        self.dicomMetaTagList = mi_utils.DEFAULT_DICOM_META_TAG_LIST
        self.QUIET = False
        #
        self._logger = None


    ### ----------------------------------------------------------------------------------------------------------------
    ### Overriding methods
    ### ----------------------------------------------------------------------------------------------------------------
    def __hash__(self):
        return hash((self.subjID, self.dataRoot))

    def __eq__(self, other):
        try:
            return (self.subjID == other.subjID) & \
                   (self.dataRoot == other.dataRoot)
        except AttributeError:
            return False

    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        return self.getPrefix_Number()[1] < other.getPrefix_Number()[1]

    def str(self):
        return f"{self.subjID} at {self.dataRoot}"

    ### ----------------------------------------------------------------------------------------------------------------
    ### Logging
    ### ----------------------------------------------------------------------------------------------------------------
    @property
    def logger(self):
        if self._logger is None:
            rr = os.path.split(self.dataRoot)[1]
            self._logger = logging.getLogger(f"{rr}/{self.subjID}")
            self._logger.setLevel(logging.INFO)
            fh = logging.FileHandler(os.path.join(self.getMetaDir(), f'{self.subjID}.log'))
            fh.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s', datefmt='%d-%b-%y %H:%M:%S'))
            self._logger.addHandler(fh)
            if not self.QUIET:
                self._logger.addHandler(logging.StreamHandler())
        return self._logger


    ### ----------------------------------------------------------------------------------------------------------------
    ### Methods
    ### ----------------------------------------------------------------------------------------------------------------
    def initDirectoryStructure(self):
        if os.path.isdir(self.getTopDir()):
            self.logger.info(f"Study participant {self.subjID} exists at {self.getTopDir()}. Updating directory structure")
        os.makedirs(self.getTopDir(), exist_ok=True)
        self.getDicomsDir()
        self.getMetaDir()
        self.logger.info(f"Directory structure correct for {self.subjID} at {self.getTopDir()}.")

    def getPrefix_Number(self):
        return splitSubjID(self.subjID)

    ### LOADING
    def loadDicomsToSubject(self, dicomFolderToLoad, anonName=None, HIDE_PROGRESSBAR=False):
        self.initDirectoryStructure()
        self.logger.info('LoadDicoms(%s, %s)'%(dicomFolderToLoad, self.getDicomsDir()))
        d0, dI = self.countNumberOfDicoms(), mi_utils.countFilesInDir(dicomFolderToLoad)
        spydcm.dcmTK.organiseDicoms(dicomFolderToLoad, self.getDicomsDir(), anonName=anonName, HIDE_PROGRESSBAR=HIDE_PROGRESSBAR)
        dO = self.countNumberOfDicoms()
        self.logger.info(f"Initial number of dicoms: {d0}, number to load: {dI}, final number dicoms: {dO}")

    ### FOLDERS / FILES ------------------------------------------------------------------------------------------------
    def exists(self):
        return os.path.isdir(self.getTopDir())

    def getTopDir(self):
        return os.path.join(self.dataRoot, self.subjID)

    def _getDir(self, listOfDirsBeyondStudyDir, BUILD_IF_NEED=True):
        dd = os.path.join(self.getTopDir(), *listOfDirsBeyondStudyDir)
        if not os.path.isdir(dd):
            if BUILD_IF_NEED & self.BUILD_DIR_IF_NEED:
                if not os.path.isdir(self.getTopDir()):
                    raise IOError(' %s does not exist'%(self.getTopDir()))
                os.makedirs(dd, exist_ok=True)
        return dd

    def getMetaDir(self):
        return self._getDir([META])

    def getRawDir(self):
        return self._getDir([RAW])
    
    def getDicomsDir(self):
        dirName = self._getDir([RAW, DICOM])
        return dirName
    
    ### META STUFF -----------------------------------------------------------------------------------------------------
    def getSeriesMetaCSV(self):
        return os.path.join(self.getMetaDir(), 'ScanSeriesInfo.csv')

    def getSeriesMetaAsDataFrame(self):
        return pd.read_csv(self.getSeriesMetaCSV(),  encoding="ISO-8859-1")

    def buildSeriesDataMetaCSV(self):
        seInfoList = []
        dcmStudies = spydcm.dcmTK.ListOfDicomStudies.setFromDirectory(self.getDicomsDir(), HIDE_PROGRESSBAR=True)
        for dcmStudy in dcmStudies:
            for dcmSE in dcmStudy:
                seInfoList.append(dcmSE.getSeriesInfoDict())
        df = pd.DataFrame(data=seInfoList)
        df.to_csv(self.getSeriesMetaCSV())
        self.logger.info('buildSeriesDataMetaCSV')

    def printDicomsInfo(self):
        dicomFolderList = self.getDicomFoldersListStr(False)
        print(str(self))
        ss = ["    " + i for i in dicomFolderList]
        print("\n".join(ss))
        print("")

    def askUserForDicomSeriesNumber(self):
        self.printDicomsInfo()
        seNum = input("Enter the dicom series number: ")
        return int(seNum)

    def findDicomSeries(self, descriptionStr, excludeStr=None):
        return self.getSeriesNumbersMatchingDescriptionStr(descriptionStr, excludeStr=excludeStr)
    
    def getStartTime_EndTimeOfExam(self):
        NN = self.getListOfSeNums()
        Ns = min(NN)
        Ne = max([i for i in NN if i < 99])
        return self.getStartTimeForSeriesN_HHMMSS(Ns), self.getStartTimeForSeriesN_HHMMSS(Ne)

    def getTimeTakenForSeriesN(self, N, df=None):
        if df is None:
            df = self.getSeriesMetaAsDataFrame()
        return list(df.loc[df['SeriesNumber']==N,'ScanDuration'])[0]

    def getHRForSeriesN(self, N, df=None):
        if df is None:
            df = self.getSeriesMetaAsDataFrame()
        return list(df.loc[df['SeriesNumber']==N,'HeartRate'])[0]

    def getStartTimeForSeriesN_HHMMSS(self, N, df=None):
        if df is None:
            df = self.getSeriesMetaAsDataFrame()
        return list(df.loc[df['SeriesNumber']==N,'StartTime'])[0]

    def getDifferenceBetweenStartTimesOfTwoScans_s(self, seN1, seN2):
        df = self.getSeriesMetaAsDataFrame()
        t1 = self.getStartTimeForSeriesN_HHMMSS(seN1, df)
        t2 = self.getStartTimeForSeriesN_HHMMSS(seN2, df)
        t1 = datetime.datetime.strptime(str(t1), '%H%M%S.%f')
        t2 = datetime.datetime.strptime(str(t2), '%H%M%S.%f')
        return (t2-t1).seconds

    def getTotalScanTime(self):
        se = self.getListOfSeNums()
        se = [i for i in se if i < 1000]
        s1 = self.getDifferenceBetweenStartTimesOfTwoScans_s(min(se), max(se))
        s2 = self.getTimeTakenForSeriesN(max(se))
        return s1 + s2

    def findDicomSeries(self, descriptionStr):
        return self.getSeriesNumbersMatchingDescriptionStr(descriptionStr)

    def getSeriesNumbersMatchingDescriptionStr(self, descriptionStr): # FIXME what if mult studies
        dcmStudy = spydcm.dcmTK.DicomStudy.setFromDirectory(self.getDicomsDir(), HIDE_PROGRESSBAR=True, ONE_FILE_PER_DIR=True)
        dOut = {}
        for iSeries in dcmStudy:
            if descriptionStr.lower() in iSeries.getTag('SeriesDescription').lower():
                dOut[iSeries.getTag('SeriesNumber', ifNotFound='#')] = iSeries.getSeriesOutDirName()
        return dOut

    def getSeriesMetaValue(self, seNum, varName):
        """
        :param seNum:
        :param varName: from : EchoTime FlipAngle HeartRate
                                InPlanePhaseEncodingDirection InternalPulseSequenceName PulseSequenceName
                                 RepetitionTime ScanDuration SeriesDescription
                                 SeriesNumber SpacingBetweenSlices StartTime
                                 dCol dRow dSlice dTime
                                 nCols nRow nSlice nTime
        :return:
        """
        df = self.getSeriesMetaAsDataFrame()
        return list(df.loc[df['SeriesNumber'] == seNum, varName])[0]

    def getMetaTagsFile(self, suffix=""):
        return os.path.join(self.getMetaDir(), "%sTags%s.json" % (self.subjID, suffix))

    def setTagValue(self, tag, value, suffix=""):
        self.updateMetaFile({tag:value}, suffix)

    def getMetaDict(self, suffix=""):
        ff = self.getMetaTagsFile(suffix)
        dd = {}
        if os.path.isfile(ff):
            dd = spydcm.dcmTools.parseJsonToDictionary(ff)
        return dd

    def getTagValue(self, tag, NOT_FOUND=None, metaSuffix=""):
        try:
            return self.getMetaDict(metaSuffix).get(tag, NOT_FOUND)
        except OSError as e:
            if NOT_FOUND is not None:
                return NOT_FOUND
            else:
                raise e

    def updateMetaFile(self, metaDict, metasuffix=""):
        dd = self.getMetaDict(metasuffix)
        dd.update(metaDict)
        spydcm.dcmTools.writeDictionaryToJSON(self.getMetaTagsFile(metasuffix), dd)
        self.logger.info('updateMetaFile')

    def buildDicomMeta(self):
        # this uses pydicom - so tag names are different.
        ddFull = {}
        dcmStudies = spydcm.dcmTK.ListOfDicomStudies.setFromDirectory(self.getDicomsDir(), HIDE_PROGRESSBAR=True)
        for dcmStudy in dcmStudies:
            ddFull.update(dcmStudy.getStudySummaryDict())
        self.updateMetaFile(ddFull)

    def countNumberOfDicoms(self):
        return mi_utils.countFilesInDir(self.getDicomsDir())
    
    def getDicomSeriesDir_Description(self, seriesDescription):
        dd = self.getSeriesNumbersMatchingDescriptionStr(seriesDescription)
        seNs = dd.keys()
        seN = min(seNs)
        return self.getDicomSeriesDir(seN)
    
    def getDicomSeriesDir(self, seriesNum, seriesUID=None):
        dcmStudies = spydcm.dcmTK.ListOfDicomStudies.setFromDirectory(self.getDicomsDir(), ONE_FILE_PER_DIR=True, HIDE_PROGRESSBAR=True)
        if seriesUID is not None:
            for dcmStudy in dcmStudies:
                dcmSeries = dcmStudy.getSeriesByUID()
                if dcmSeries is not None:
                    break
            if dcmSeries is None:
                raise ValueError("## ERROR: Series with UID: %s NOT FOUND"%(seriesUID))
        else:
            for dcmStudy in dcmStudies:
                dcmSeries = dcmStudy.getSeriesByID(seriesNum)
                if dcmSeries is not None:
                    break
            if dcmSeries is None:
                raise ValueError("## ERROR: Series with SE number: %s NOT FOUND"%(str(seriesNum)))
        dirName = dcmSeries.getRootDir()
        return dirName

    def getDicomFile(self, seriesNum, instanceNum=1):
        #FIXME Note - at some point the files were named incorrectly - this has to work around this... Could be better
        # (and the number of leading zeros changed)
        # possible fix - work it out on per subject basis
        dicomf = os.path.join(self.getDicomSeriesDir(seriesNum), 'IM-%04d-%04d.dcm'%(seriesNum, instanceNum))
        if not os.path.isfile(dicomf):
            dicomf = os.path.join(self.getDicomSeriesDir(seriesNum),
                                  'IM-%04d-%04d.dcm' % (1, instanceNum))
        if not os.path.isfile(dicomf):
            dicomf = os.path.join(self.getDicomSeriesDir(seriesNum),
                                  'IM-%05d-%05d.dcm' % (seriesNum, instanceNum))
        return dicomf

    def getDicomFoldersListStr(self, FULL=True, excludeSeNums=None):
        dFolders = []
        dcmStudies = spydcm.dcmTK.ListOfDicomStudies.setFromDirectory(self.getDicomsDir(), ONE_FILE_PER_DIR=True, HIDE_PROGRESSBAR=True)
        for dcmStudy in dcmStudies:
            for iSeries in dcmStudy:
                dFolders.append(iSeries.getRootDir())
        dS = sorted(dFolders, key=spydcm.dcmTools.instanceNumberSortKey)
        if not FULL:
            dS = [os.path.split(i)[1] for i in dS]
            return dS
        if excludeSeNums is None:
            excludeSeNums = []
        seN = []
        for i in dS:
            try:
                seN.append(int(i.split('_')[0][2:]))
            except ValueError:
                pass
        dcmDirList = [self.getDicomSeriesDir(i) for i in seN if i not in excludeSeNums]
        dcmDirList = sorted(dcmDirList, key=spydcm.dcmTools.instanceNumberSortKey)
        return dcmDirList

    def getListOfSeNums(self):
        se = []
        for ff in self.getDicomFoldersListStr(FULL=False):
            try:
                sn = int(ff.split('_')[0].replace('SE',''))
                se.append(sn)
            except ValueError:
                pass
        return se

    def getStudyID(self):
        studyID = self.getTagValue("StudyID")
        if studyID == "0":
            studyID = self.getTagValue("ScannerStudyID")
        return studyID
    
    def getSeriesDescriptionsStr(self):
        return ','.join(self.getDicomFoldersListStr(FULL=False))


    def getStudyDate(self, RETURN_Datetime=False):
        dos = self.getTagValue('StudyDate')
        if RETURN_Datetime:
            spydcm.dcmTools.dbDateToDateTime(dos)
        return dos

    def getInfoStr(self):
        # Return values_list, info_keys:
        #   list of values for info keys (+ age). 
        #   header keys
        infoKeys = ['PatientBirthDate', 'PatientID', 'PatientName', 'PatientSex',
                    'StudyDate', 'StudyDescription', 'StudyInstanceUID', 'StudyID', 'Consent']
        mm = self.getMetaDict()
        aa = '%5.2f'%(self.getAge())
        return [mm.get(i, "Unknown") for i in infoKeys]+[aa], infoKeys + ['Age']

    # ------------------------------------------------------------------------------------------
    def getSummary_list(self):
        hh = ["SubjectID","PatientID","Gender","StudyDate","NumberOfSeries","SERIES_DECRIPTIONS"]
        parts = [self.subjID, self.getTagValue('PatientID'), 
                self.getTagValue('PatientSex'), self.getTagValue('StudyDate'), 
                len(self.getTagValue('Series')), self.getSeriesDescriptionsStr()]
        ss = [str(i) for i in parts]
        return hh, ss

    def getAge(self):
        """
        This returns a float, and is slightly wrong in account of leap years.
        This is intentional.
        :return: years - float
        """
        dd = self.getMetaDict()
        try:
            birth = dd["PatientBirthDate"]
            study = dd["StudyDate"]
            return (spydcm.dcmTools.dbDateToDateTime(study) - spydcm.dcmTools.dbDateToDateTime(birth)).days / 365.0
        except (KeyError, ValueError):
            return np.nan

    def getGender(self):
        return self.getMetaDict()['PatientSex']
    
    def isMale(self):
        sex = self.getGender()
        return sex.strip().lower() == 'm'

    # ------------------------------------------------------------------------------------------------------------------
    def zipUpSubject(self, outputDirectory):
        archive_name = os.path.join(outputDirectory, self.subjID)
        zipfileOut = shutil.make_archive(archive_name, 'zip', root_dir=self.getTopDir())
        self.logger.info(f'Zipped subject to {zipfileOut}')
        return zipfileOut


# ====================================================================================================
#       LIST OF SUBJECTS CLASS
# ====================================================================================================
class SubjectList(list):
    """
    Container for a list of subjects
    """
    def __init__(self, subjList=[]):
        super().__init__(i for i in subjList)


    @classmethod
    def setByDirectory(cls, rootDirectory, subjectPrefix=None):
        listOfSubjects = getAllSubjects(rootDirectory, subjectPrefix)
        return cls(listOfSubjects)

    def reduceToExist(self):
        toRemove = []
        for i in self:
            if not i.exists():
                toRemove.append(i)
        for i in toRemove:
            self.remove(i)

    def filterSubjectListByDOS(self, dateOfScan_YYYYMMDD, dateEnd_YYYYMMDD=None): #TODO
        """
        Take list, return only those that match DOS or between start and end (inclusive) if dateEnd given
        :param subjList:
        :param dateOfScan_YYYYMMDD: str
        :param dateEnd_YYYYMMDD: str - optional 
        :return:
        """
        filteredMatchList = []
        for isO in self:
            iDOS = isO.getTagValue('StudyDate')
            try:
                if iDOS == dateOfScan_YYYYMMDD:
                    filteredMatchList.append(isO)
            except ValueError: # maybe don't have tag, or wrong format
                continue
        return SubjectList(filteredMatchList)

    def findSubjMatchingStudyID(self, studyID):
        """
        :param studyID (or examID): int
        :return: mi_subject
        """
        for iSubj in self:
            try:
                if int(iSubj.getTagValue("StudyID")) == studyID:
                    return iSubj
            except ValueError:
                pass
        return None
    
    def findSubjMatchingPatientID(self, patientID, dateOfScan_YYYYMMDD=None):
        """
        :param patientID:
        :param dateOfScan_YYYY_MM_DD: list of ints for DOS to fix ambiguity
        :return: SubjectList
        """
        patientID = str(patientID)
        matchList = SubjectList()
        for iSubj in self:
            try:
                if iSubj.getTagValue("PatientID") == patientID:
                    matchList.append(iSubj)
            except ValueError:
                pass
        if (len(matchList)>1) & (dateOfScan_YYYYMMDD is not None):
            return matchList.filterSubjectListByDOS(dateOfScan_YYYYMMDD)
        return matchList

    def findSubjMatchingName(self, nameStr, dateOfScan_YYYYMMDD=None, decodePassword=None):
        """
        :param nameStr:
        :param dateOfScan_YYYYMMDD: if given will use to filter list matching name
        :return: SubjectList
        """
        nameStr_l = nameStr.lower()
        matchList = SubjectList()
        for iSubj in self:
            iName = iSubj.getTagValue("NAME", UNKNOWN)
            if decodePassword is not None:
                iName = mi_utils.decodeString(iName, decodePassword).lower()
            try:
                if nameStr_l in iName:
                    matchList.append(iSubj)
            except ValueError:
                pass
        if (len(matchList)>1) & (dateOfScan_YYYYMMDD is not None):
            return matchList.filterSubjectListByDOS(dateOfScan_YYYYMMDD)
        return matchList



### ====================================================================================================================
### ====================================================================================================================
### ====================================================================================================================
def splitSubjID(s):
    prefix = s.rstrip('0123456789')
    number = int(s[len(prefix):])
    return prefix, number

def getNumberFromSubjID(subjID):
    return splitSubjID(subjID)[1]

def guessSubjectPrefix(rootDir):
    allDir = [i for i in os.listdir(rootDir) if os.path.isdir(os.path.join(rootDir, i))]
    allDir_subj = {}
    for i in allDir:
        prefix, N = splitSubjID(i)
        allDir_subj.setdefault(prefix, []).append(N)
    options = list(allDir_subj.keys())
    counts = [len(allDir_subj[i]) for i in options]
    return options[np.argmax(counts)]

def getAllSubjects(DATA_DIR, subjectPrefix=None):
    if subjectPrefix is None:
        subjectPrefix = guessSubjectPrefix(DATA_DIR)
    allDir = os.listdir(DATA_DIR)
    subjObjList = [AbstractSubject(i, projectRoot=DATA_DIR) for i in allDir]
    subjObjList = [i for i in subjObjList if i.exists()]
    return sorted(subjObjList)

def buildSubjectID(subjN, prefix):
    return f"{prefix}{subjN:06d}"

def getNextSubjN(dataRootDir, prefix):
    allNums = [int(i[len(prefix):]) for i in os.listdir(dataRootDir) if i.startswith(prefix)]
    try:
        return max(allNums)+1
    except ValueError:
        return 0

def getNextSubjID(dataRootDir, prefix):
    return buildSubjectID(getNextSubjN(dataRootDir, prefix), prefix)

def subjNListToSubjObj(subjNList, dataRoot, subjPrefix, SubjClass=AbstractSubject, CHECK_EXIST=True):
    subjList = SubjectList([SubjClass(iN, dataRoot, subjPrefix) for iN in subjNList])
    if CHECK_EXIST:
        subjList.reduceToExist()
    return subjList

def loadNewSubject(dicomDirToLoad, dataRoot, subjPrefix, SubjClass=AbstractSubject, subjID=None):
    if not os.path.isdir(dicomDirToLoad):
        raise IOError(" Load dir does not exist")
    if spydcm.returnFirstDicomFound(dicomDirToLoad) is None:
        raise IOError(f"Can not find valid dicoms under {dicomDirToLoad}")
    if not os.path.isdir(dataRoot):
        raise IOError(" Destination does not exist")
    if subjID is None:
        subjID = getNextSubjID(dataRoot, subjPrefix)
    newSubj = SubjClass(subjID, dataRoot)
    newSubj.initDirectoryStructure()
    newSubj.loadDicomsToSubject(dicomDirToLoad)
    newSubj.buildDicomMeta()
    newSubj.buildSeriesDataMetaCSV()
    #
    return newSubj
