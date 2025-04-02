import os
import base64
import csv
import datetime

from hurahura.mi_config import MIResearch_config



DEFAULT_DICOM_META_TAG_LIST_STUDY = ["AccessionNumber",
                                "InstitutionName",
                                "BodyPartExamined",
                                "MagneticFieldStrength",
                                "Manufacturer",
                                "ManufacturerModelName",
                                "Modality",
                                "PatientBirthDate",
                                "PatientID",
                                "PatientName",
                                "PatientSex",
                                "PatientAge",
                                "PatientWeight",
                                "ProtocolName",
                                "ReceiveCoilName",
                                "ScannerStudyID",
                                "SoftwareVersions",
                                "StationName",
                                "StudyDate",
                                "StudyDescription",
                                "StudyID",
                                "StudyInstanceUID",
                                "StudyTime"]

DEFAULT_DICOM_META_TAG_LIST_SERIES = [
                                "AcquiredResolution",
                                "AcquiredTemporalResolution",
                                "AcquisitionMatrix",
                                "AcquisitionTime",
                                "DicomFileName",
                                "EchoTime",
                                "FlipAngle",
                                "HeartRate",
                                "InPlanePhaseEncodingDirection",
                                "InternalPulseSequenceName",
                                "MagneticFieldStrength",
                                "Manufacturer",
                                "ManufacturerModelName",
                                "PixelBandwidth",
                                "PulseSequenceName",
                                "ReconstructionDiameter",
                                "RepetitionTime",
                                "ScanDuration",
                                "ScanningSequence",
                                "SeriesDescription",
                                "SeriesNumber",
                                "SoftwareVersions",
                                "SpacingBetweenSlices",
                                "StudyDate"]


DEFAULT_DICOM_TIME_FORMAT = "%H%M%S" # TODO to config (and above) - or from spydcmtk

abcList = 'abcdefghijklmnopqrstuvwxyz'
UNKNOWN = 'UNKNOWN'
META = "META"
RAW = "RAW"
DICOM = "DICOM"
OTHER = "OTHER"

#==================================================================

#==================================================================
class DirectoryStructure():
    def __init__(self, name, childrenList=[]) -> None:
        self.name = name
        self.childrenList = childrenList
    
    def __str__(self) -> str:
        return f"{self.name} with children: {self.childrenList}"

class DirectoryStructureTree(list):
    def __init__(self) -> None:
        super().__init__()

    def __str__(self) -> str:
        ss = ''
        for i in self:
            ss += str(i)+'\n'
        return ss

    def addNewStructure(self, name_or_list):
        if type(name_or_list) == list:
            self._addTopLevelDirectory(name_or_list[0])
            for k1 in range(1, len(name_or_list)):
                self._addSecondLevelDirectory(name_or_list[0], name_or_list[k1])
        else:
            self._addTopLevelDirectory(name_or_list)

    def _addTopLevelDirectory(self, name):
        if not self.isTopLevelName(name):
            self.append(DirectoryStructure(name, []))
    
    def _addSecondLevelDirectory(self, nameTopLevel, nameSecondLevel):
        if not self.isSecondLevelName(nameTop=nameTopLevel, nameSecond=nameSecondLevel):
            for i in self:
                if i.name == nameTopLevel:
                    i.childrenList.append(nameSecondLevel)

    def isTopLevelName(self, name):
        for i in self:
            if i.name == name:
                return True
        return False
    
    def isSecondLevelName(self, nameTop, nameSecond):
        for i in self:
            if i.name == nameTop:
                for i2 in i.childrenList:
                    if i2 == nameSecond:
                        return True
        return False


def _getDefautDirectoryStructureTree():
    """This builds a Directory tree structure from the config file input

    Returns:
        DirectoryStructureTree: class of Directory trees structure used by misubject
    """
    DEFAULT_DIRECTORY_STRUCTURE_TREE = DirectoryStructureTree()
    for i in MIResearch_config.directory_structure:
        DEFAULT_DIRECTORY_STRUCTURE_TREE.addNewStructure(i)
    return DEFAULT_DIRECTORY_STRUCTURE_TREE

def buildDirectoryStructureTree(listOfExtraSubfolders=[]):
    """This will build the directory structure for a project using the structure
        found in config file and any added subfolder names

    Args:
        listOfExtraSubfolders (list): A list of subfolders, if an entry is itself a list, 
            then the first item of that entry is the toplevel subfolder 
            and the following items are subfolders of that toplevel folder.
            Default: empty list                                    
            Note: A default structure is always used of:
            | - META
            | - RAW 
                    | - DICOM
    """
    #  first remove any conflists with default list:
    DirectoryTree = _getDefautDirectoryStructureTree()
    for i in listOfExtraSubfolders:
        DirectoryTree.addNewStructure(i)
    return DirectoryTree


def getDataRootDir():
    return MIResearch_config.data_root_dir
#==================================================================
#==================================================================
def countFilesInDir(dirName):
    N = 0
    if os.path.isdir(dirName):
        for _, _, filenames in os.walk(dirName):  # @UnusedVariable
            N += len(filenames)
    return N

def datetimeToStrTime(dateTimeVal, strFormat=DEFAULT_DICOM_TIME_FORMAT):
    return dateTimeVal.strftime(strFormat)

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
    enc = base64.urlsafe_b64decode(encStr+'==').decode()
    for i in range(len(enc)):
        key_c = passcode[i % len(passcode)]
        dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
        dec.append(dec_c)
    return "".join(dec)


def readFileToListOfLines(fileName, commentSymbol='#'):
    ''' Read file - return list - elements made up of each line
        Will split on "," if present
        Will skip starting with #
    '''
    with open(fileName, 'r') as fid:
        lines = fid.readlines()
    lines = [l.strip('\n') for l in lines]
    lines = [l for l in lines if len(l) > 0]
    lines = [l for l in lines if l[0]!=commentSymbol]
    lines = [l.split(',') for l in lines]
    return lines


def subjFileToSubjN(subjFile):
    allLines = readFileToListOfLines(subjFile)
    try:
        return [int(i[0]) for i in allLines]
    except ValueError:
        tf = [i.isnumeric() for i in allLines[0][0]]
        first_numeric = tf.index(True)
        return [int(i[0][first_numeric:]) for i in allLines]


def writeCSVFile(data, header, csvFile, FIX_NAN=False):
    with open(csvFile, 'w') as fout:
        csvWriter = csv.writer(fout, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        #first write column headers
        if header is not None:
            csvWriter.writerow(header)
        for iRow in data:
            if FIX_NAN:
                iRow = ['' if i=='nan' else i for i in iRow]
            csvWriter.writerow(iRow)
    return csvFile


def timeToDatetime(timeStr):
    try:
        iDatetime = datetime.datetime.strptime(timeStr, '%H%M%S.%f')
    except ValueError:
        iDatetime = datetime.datetime.strptime(timeStr, '%H%M%S')
    return iDatetime
#==================================================================
class SubjPrefixError(Exception):
    ''' SubjPrefixError
            If errors to do with the subject prefix '''
    def __init__(self, msg2=''):
        self.msg = 'SubjPrefixError: please provide as imput.' + '\n' + msg2
    def __str__(self):
        return self.msg
