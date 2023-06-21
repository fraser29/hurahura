#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 26 10:59:36 2018

@author: Fraser M Callaghan

Classes for building standardised imaging projects. 
Adapted for general use from KMR project. 


"""


import os
import base64
import shutil
import numpy as np
import datetime
import pandas as pd
## Local imports
from spydcmtk import dcmTK

abcList = 'abcdefghijklmnopqrstuvwxyz'

physiologyDataDir = '/mnt/x-bigdata/MRI-Proc/Vol03/ScannerPhysiologicalData'

DEFAULT_DICOM_META_TAG_LIST = ["BodyPartExamined",
                                "MagneticFieldStrength",
                                "Manufacturer",
                                "ManufacturerModelName",
                                "Modality",
                                "PatientBirthDate",
                                "PatientID",
                                "PatientName",
                                "PatientSex",
                                "ReceiveCoilName",
                                "SoftwareVersions",
                                "StudyDate",
                                "StudyDescription",
                                "StudyID",
                                "StudyInstanceUID"]


class DirectoryStructure(object):
    def __init__(self, name, childrenList=[]) -> None:
        super().__init__()
        self.name = name
        self.childrenList = childrenList

class DirectoryStructureTree():
    def __init__(self, topList) -> None:
        self.topList = topList


DEFAULT_DIRECTORY_STRUCTURE_TREE = DirectoryStructureTree([DirectoryStructure('RAW', [DirectoryStructure('DICOM')]),
                                                            DirectoryStructure('META')])


# ====================================================================================================
#       HELPERS
# ====================================================================================================


# ====================================================================================================
#       ABSTRACT SUBJECT CLASS
# ====================================================================================================
class AbstractSubject(object):
    """
    An abstract subject controlling most basic structure
    """
    def __init__(self, subjectFullID, 
                        projectRoot, 
                        DIRECTORY_STURCTURE_TREE=DEFAULT_DIRECTORY_STRUCTURE_TREE) -> None:
        self.subjID = subjectFullID
        self.dataRoot = projectRoot
        self.DIRECTORY_STURCTURE_TREE = DIRECTORY_STURCTURE_TREE
        self.logfile = None
        self.BUILD_DIR_IF_NEED = True
        self.dicomMetaTagList = DEFAULT_DICOM_META_TAG_LIST


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
        try:
            dos1 = dcmTK.dcmTools.dbDateToDateTime(self.getTagValue('StudyDate'))
            dos2 = dcmTK.dcmTools.dbDateToDateTime(other.getTagValue('StudyDate'))
        except AttributeError:
            dos1 = 1
            dos2 = 1
        if dos1 == dos2:
            return int(self.getTagValue('StudyID')) < int(self.getTagValue('StudyID'))
        return dos1 < dos2

    ### ----------------------------------------------------------------------------------------------------------------
    ### Methods
    ### ----------------------------------------------------------------------------------------------------------------
    def log(self, message, LEVEL='INFO', STREAM=True):
        if self.logfile is None:
            self.logfile = os.path.join(self.getMetaDir(), '%s.log'%(self.subjID))
        with open(self.logfile, 'a+') as fid:
            sNow = datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S")
            strOut =  '%s|%s|%s'%(sNow, LEVEL, message)
            fid.write('%s\r\n'%(strOut))
        if STREAM:
            print(strOut)

    def initDirectroyStructure(self):
        os.makedirs(self.getTopDir(), exist_ok=True)
        self.getDicomsDir()
        self.getMetaDir()

    def getSeriesMetaCSV(self):
        return os.path.join(self.getMetaDir(), 'ScanSeriesInfo.csv')

    def buildSeriesDataMetaCSV(self):
        seInfoList = []
        dcmStudy = dcmTK.DicomStudy.setFromDirectory(self.getDicomsDir(), TQDM_HIDE=True)
        for dcmSE in dcmStudy:
            seInfoList.append(dcmSE.getSeriesInfoDict())
        df = pd.DataFrame(data=seInfoList)
        df.to_csv(self.getSeriesMetaCSV())
        self.log('buildSeriesDataMetaCSV')

    def getStartTime_EndTimeOfExam(self):
        NN = self.getListOfSeNums()
        Ns = min(NN)
        Ne = max([i for i in NN if i < 99])
        return self.getStartTimeForSeriesN_HHMMSS(Ns), self.getStartTimeForSeriesN_HHMMSS(Ne)

    def getTimeTakenForSeriesN(self, N, df=None):
        if df is None:
            df = pd.read_csv(self.getSeriesMetaCSV(),  encoding="ISO-8859-1")
        return list(df.loc[df['SeriesNumber']==N,'ScanDuration'])[0]

    def getHRForSeriesN(self, N, df=None):
        if df is None:
            df = pd.read_csv(self.getSeriesMetaCSV(),  encoding="ISO-8859-1")
        return list(df.loc[df['SeriesNumber']==N,'HeartRate'])[0]

    def getStartTimeForSeriesN_HHMMSS(self, N, df=None):
        if df is None:
            df = pd.read_csv(self.getSeriesMetaCSV(),  encoding="ISO-8859-1")
        return list(df.loc[df['SeriesNumber']==N,'StartTime'])[0]

    def getDifferenceBetweenStartTimesOfTwoScans_s(self, seN1, seN2):
        df = pd.read_csv(self.getSeriesMetaCSV(), encoding="ISO-8859-1")
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

    def getSeriesNumbersMatchingDescriptionStr(self, descriptionStr):
        dcmStudy = dcmTK.DicomStudy.setFromDirectory(self.getDicomsDir(), TQDM_HIDE=True, ONE_FILE_PER_DIR=True)
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
        df = pd.read_csv(self.getSeriesMetaCSV(), encoding="ISO-8859-1")
        return list(df.loc[df['SeriesNumber'] == seNum, varName])[0]

    ### LOADING
    def loadDicomsToSubject(self, dicomFolderToLoad, anonName=None, TQDM_HIDE=False):
        self.initDirectroyStructure()
        dcmTK.organiseDicoms(dicomFolderToLoad, self.getDicomsDir(), anonName=anonName, HIDE_PROGRESSBAR=TQDM_HIDE)
        self.log('LoadDicoms(%s, %s)'%(dicomFolderToLoad, self.getDicomsDir()))

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
                try:
                    os.makedirs(dd)
                except OSError:
                    pass
        return dd

    def getMetaDir(self):
        return self._getDir(["META"])

    def getMetaTagsFile(self, suffix=""):
        return os.path.join(self.getMetaDir(), "%sTags%s.json" % (self.subjID, suffix))

    def setTagValue(self, tag, value, suffix=""):
        self.updateMetaFile({tag:value}, suffix)

    def getMetaDict(self, suffix=""):
        ff = self.getMetaTagsFile(suffix)
        dd = {}
        if os.path.isfile(ff):
            dd = dcmTK.dcmTools.parseJsonToDictionary(ff)
        return dd

    def getTagValue(self, tag, NOT_FOUND=None, metaSuffix=""):
        try:
            return self.getMetaDict(metaSuffix).get(tag, NOT_FOUND)
        except OSError as e:
            if NOT_FOUND is not None:
                return NOT_FOUND
            else:
                raise e

    # def setName(self, NAME, FIRST_NAMES):
    #     """
    #     funct to add name after (will encode)
    #     :param NAME:
    #     :param FIRST_NAMES:
    #     :return:
    #     """
    #     dd = {'NAME': encodeString(NAME, xxfyz),
    #           'FIRST_NAMES': encodeString(FIRST_NAMES, xxfyz)}
    #     self.updateMetaFile(dd)

    # def getName(self):
    #     return decodeString(self.getTagValue("NAME", nameUnknown), xxfyz)

    # def getName_FirstNames(self):
    #     return decodeString(self.getTagValue("NAME", nameUnknown), xxfyz), \
    #            decodeString(self.getTagValue("FIRST_NAMES", nameUnknown), xxfyz)

    def updateMetaFile(self, metaDict, metasuffix=""):
        dd = self.getMetaDict(metasuffix)
        dd.update(metaDict)
        dcmTK.dcmTools.writeDictionaryToJSON(self.getMetaTagsFile(metasuffix), dd)
        self.log('updateMetaFile')

    def studyDicomTagsToMeta(self):
        # this uses pydicom - so tag names are different.
        dcmStudy = dcmTK.DicomStudy.setFromDirectory(self.getDicomsDir(), TQDM_HIDE=True)
        dd = dcmStudy.getStudySummaryDict()
        self.updateMetaFile(dd)

    def setArchived(self):
        self.updateMetaFile({'ARCHIVED': 'True'})

    def isArchived(self):
        return self.getTagValue('ARCHIVED', 'False') == 'True'

    def getRawDir(self):
        return self._getDir(["RAW"])
    
    def getDicomsDir(self, swapRoot=None):
        dirName = self._getDir(["RAW", "DICOM"])
        if swapRoot:
            dirName = dirName.replace(self.dataRoot, swapRoot)
        return dirName
    
    def getDicomSeriesDir(self, seriesNum, swapRoot=None, seriesUID=None):
        dcmStudy = dcmTK.DicomStudy.setFromDirectory(self.getDicomsDir(), TQDM_HIDE=True, ONE_FILE_PER_DIR=True)
        if seriesUID is not None:
            dcmSeries = dcmStudy.getSeriesByUID()
            if dcmSeries is None:
                raise ValueError("## ERROR: Series with UID: %s NOT FOUND"%(seriesUID))
        else:
            dcmSeries = dcmStudy.getSeriesByID(seriesNum)
            if dcmSeries is None:
                raise ValueError("## ERROR: Series with SE number: %s NOT FOUND"%(str(seriesNum)))
        dirName = dcmSeries.getRootDir()
        nFile = len(os.listdir(dirName))
        if (nFile<1) & (swapRoot is not None):
            dirName = dirName.replace(self.dataRoot, swapRoot)
        return dirName

    def getDicomFoldersListStr(self, FULL=True, excludeSeNums=None, swapRoot=None):
        dcmStudy = dcmTK.DicomStudy.setFromDirectory(self.getDicomsDir(), ONE_FILE_PER_DIR=True, TQDM_HIDE=True)
        dFolders = [i.getRootDir() for i in dcmStudy]
        # dFolders = [i for sublist in dFolders for i in sublist]
        dS = sorted(dFolders, key=dcmTK.dcmTools.instanceNumberSortKey)
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
        dcmDirList = sorted(dcmDirList, key=dcmTK.dcmTools.instanceNumberSortKey)
        if swapRoot is not None:
            dcmDirList = [i.replace(self.dataRoot, swapRoot) for i in dcmDirList]
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

    # def getPtAndNormFromDicomSeries(self, seriesNum, swapRoot=None):
    #     dicomf = mrtk.returnFirstDcmFound(self.getDicomSeriesDir(seriesNum, swapRoot))
    #     norm = mrtk.getImagePlaneNormal(dicomf)
    #     cp = mrtk.getCenterOfDicom(dicomf, RETURN_m=True)
    #     return cp, norm

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
            return (dcmTK.dcmTools.dbDateToDateTime(study) - dcmTK.dcmTools.dbDateToDateTime(birth)).days / 365.0
        except (KeyError, ValueError):
            return np.nan

    def getGender(self):
        return self.getMetaDict()['PatientSex']

    # ------------------------------------------------------------------------------------------------------------------
    def copyGatingToStudy(self):
        if "3" in self.getTagValue("MagneticFieldStrength"):
            gatingDir = os.path.join(physiologyDataDir, '3T', 'gating')
        else:
            gatingDir = os.path.join(physiologyDataDir, '1.5T', 'gating')
        if not os.path.isdir(gatingDir):
            self.log("Gating backup directory not accessible", "ERROR")
        tStart, tEnd = self.getStartTime_EndTimeOfExam()
        tStart, tEnd = str(tStart), str(tEnd)
        doScan = self.getMetaDict()['StudyDate']
        t1 = datetime.datetime.strptime(str(doScan+tStart), '%Y%m%d%H%M%S')
        t2 = datetime.datetime.strptime(str(doScan+tEnd), '%Y%m%d%H%M%S')
        gatingFiles = os.listdir(gatingDir)
        c0 = 0
        for iFile in gatingFiles:
            parts = iFile.split('_')
            fileDate = datetime.datetime.strptime(parts[-4]+parts[-3]+parts[-2], '%m%d%Y%H%M%S')
            if (fileDate < t2) and (fileDate > t1):
                shutil.copy2(os.path.join(gatingDir, iFile), self.getMetaDir())
                c0 += 1
        self.log(f"Copied {c0} gating files to Meta directory")
        
    def zipUpSubject(self, outputDirectory):
        archive_name = os.path.join(outputDirectory, self.subjID)
        zipfileOut = shutil.make_archive(archive_name, 'zip', root_dir=self.getTopDir())
        self.log(f'Zipped subject to {zipfileOut}')
        return zipfileOut



### ====================================================================================================================

def getAllSubjects(DATA_DIR):
    allDir = os.listdir(DATA_DIR)
    subjObjList = [AbstractSubject(i, projectRoot=DATA_DIR) for i in allDir]
    subjObjList = [i for i in subjObjList if i.exists()]
    return sorted(subjObjList)

class SubjectList(list):
    """
    Container for a list of subjects
    """
    def __init__(self):
        list.__init__(self)


### ====================================================================================================================
### ====================================================================================================================
### ====================================================================================================================

def filterSubjectListByDOS(subjList, dateOfScan_YYYY_MM_DD):
    """
    Take list, return only those that match DOS
    :param subjList:
    :param dateOfScan_YYYY_MM_DD: list of ints
    :return:
    """
    try:
        Y, M, D = dateOfScan_YYYY_MM_DD
    except ValueError:
        Y = int(dateOfScan_YYYY_MM_DD[:4])
        M = int(dateOfScan_YYYY_MM_DD[4:6])
        D = int(dateOfScan_YYYY_MM_DD[6:])
    filteredMatchList = []
    for isO in subjList:
        YYYYMMDD = isO.getTagValue('StudyDate')
        try:
            if (int(YYYYMMDD[:4]) == Y) & (int(YYYYMMDD[4:6]) == M) & (int(YYYYMMDD[6:]) == D):
                filteredMatchList.append(isO)
        except ValueError: # maybe don't have tag, or wrong format
            continue
    # if len(filteredMatchList) == 0:
    #     print(' ## WARNING ## filtering by DOS reduced list from %d to 0'%(len(subjList)))
    return filteredMatchList


#==================================================================
def encodeString(strIn, passcode):
    enc = []
    for i in range(len(strIn)):
        key_c = passcode[i % len(passcode)]
        enc_c = chr((ord(strIn[i]) + ord(key_c)) % 256)
        enc.append(enc_c)
    return base64.urlsafe_b64encode("".join(enc).encode()).decode()

def decodeString(encStr, passcode):
    dec = []
    enc = base64.urlsafe_b64decode(encStr).decode()
    for i in range(len(enc)):
        key_c = passcode[i % len(passcode)]
        dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
        dec.append(dec_c)
    return "".join(dec)


