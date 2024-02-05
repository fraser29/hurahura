import os
import sys
import argparse
import base64
import csv

from miresearch.mi_config import MIResearch_config



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

DEFAULT_DICOM_TIME_FORMAT = "%H%M%S" # TODO to config (and above) - or from spydcmtk

abcList = 'abcdefghijklmnopqrstuvwxyz'
UNKNOWN = 'UNKNOWN'
META = "META"
RAW = "RAW"
DICOM = "DICOM"


#==================================================================
def getDataRoot():
    """Function to return data root from configuration. 

    Returns:
        str: Path to data root - found from config
    """
    return MIResearch_config.DataRootDir

#==================================================================
class DirectoryStructure(object):
    def __init__(self, name, childrenList=[]) -> None:
        super().__init__()
        self.name = name
        self.childrenList = childrenList

class DirectoryStructureTree():
    def __init__(self, topList) -> None:
        self.topList = topList

    def addTopLevelDirectory(self, name):
        self.topList.append(DirectoryStructure(name))
    
    def addSecondLevelDirectory(self, nameTopLevel, nameSecondLevel):
        for i in self.topList:
            if i.name == nameTopLevel:
                i.childrenList.append(nameSecondLevel)

def _getDefautDirectoryStructureTree():
    DEFAULT_DIRECTORY_STRUCTURE_TREE = DirectoryStructureTree([DirectoryStructure(RAW, [DirectoryStructure(DICOM)]),
                                                                        DirectoryStructure(META)])
    return DEFAULT_DIRECTORY_STRUCTURE_TREE

def buildDirectoryStructureTree(listOfExtraSubfolders=[]):
    """This will build the directory structure for a project using a base structure and any added subfolder names

    Args:
        listOfExtraSubfolders (list): A list of subfolders, if an entry is itself a list, 
                                    then the first item of that entry is the toplevel subfolder 
                                    and the following items are subfolders of that toplevel folder.
                                    Default: empty list
    """
    #  first remove any conflists with default list:
    listOfExtraSubfolders = [i for i in listOfExtraSubfolders if i not in [RAW, META]]
    baseStructure = _getDefautDirectoryStructureTree()
    for i in listOfExtraSubfolders:
        if type(i) == list:
            baseStructure.addTopLevelDirectory(i[0])
            for k1 in range(1, len(i)):
                baseStructure.addSecondLevelDirectory(i[k1])
        else:
            baseStructure.addTopLevelDirectory(i)

#==================================================================
# Override error to show help on argparse error (missing required argument etc)
class MiResearchParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

ParentAP = MiResearchParser(add_help=False,
                                   epilog="Written Fraser M. Callaghan. MRZentrum, University Children's Hospital Zurich")

groupM = ParentAP.add_argument_group('Management Parameters')
groupM.add_argument('-config', dest='configFile', help='Path to configuration file to use.', type=str, default=None)
groupM.add_argument('-FORCE', dest='FORCE', help='force action - use with caution',
                        action='store_true')
groupM.add_argument('-QUIET', dest='QUIET', help='Suppress progress bars and logging to terminal',
                        action='store_true')
groupM.add_argument('-INFO', dest='INFO', help='Provide setup (configuration) info and exit.',
                        action='store_true')
groupM.add_argument('-DEBUG', dest='DEBUG', help='Run in DEBUG mode (save intermediate steps, increase log output)',
                        action='store_true')

SubjectInput = MiResearchParser(add_help=False)

groupS = SubjectInput.add_argument_group('Subject Definition')
groupS.add_argument('-s', dest='subjNList', help='Subject number', nargs="*", type=int, default=[])
groupS.add_argument('-sf', dest='subjNListFile', help='Subject numbers in file', type=str, default=None)
groupS.add_argument('-sR', dest='subjRange', help='Subject range', nargs=2, type=int, default=[])
groupS.add_argument('-y', dest='dataRoot', 
                    help='Path of root data directory (where subjects are stored) [default None -> may be set in config file]', 
                    type=str, default=None)
groupS.add_argument('-sPrefix', dest='subjPrefix', 
                    help='Subject prefix [default None -> will get from dataRoot]', 
                    type=str, default=None)
groupS.add_argument('-anonName', dest='anonName', 
                    help='Set to anonymise newly loaded subject. Set to true to use for WatchDirectory. [default None]', 
                    type=str, default=None)

#==================================================================
def setNList(args):
    if len(args.subjRange) == 2:
        args.subjNList = args.subjNList+list(range(args.subjRange[0], args.subjRange[1]))
    if args.subjNListFile:
        args.subjNList = args.subjNList+subjFileToSubjN(args.subjNListFile)
    # args.subjNList = sorted(list(set(args.subjNList)))
    
#==================================================================
def countFilesInDir(dirName):
    files = []
    if os.path.isdir(dirName):
        for _, _, filenames in os.walk(dirName):  # @UnusedVariable
            files.extend(filenames)
    return len(files)

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
    enc = base64.urlsafe_b64decode(encStr).decode()
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


def writeCsvFile(data, header, csvFile, FIX_NAN=False):
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

#==================================================================
class SubjPrefixError(Exception):
    ''' SubjPrefixError
            If errors to do with the subject prefix '''
    def __init__(self, msg2=''):
        self.msg = 'SubjPrefixError: please provide as imput.' + '\n' + msg2
    def __str__(self):
        return self.msg
