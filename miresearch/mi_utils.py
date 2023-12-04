import os
import base64



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

DEFAULT_DICOM_DATE_FORMAT = "%H%M%S"

#==================================================================
class DirectoryStructure(object):
    def __init__(self, name, childrenList=[]) -> None:
        super().__init__()
        self.name = name
        self.childrenList = childrenList

class DirectoryStructureTree():
    def __init__(self, topList) -> None:
        self.topList = topList

#==================================================================
def countFilesInDir(dirName):
    files = []
    if os.path.isdir(dirName):
        for _, _, filenames in os.walk(dirName):  # @UnusedVariable
            files.extend(filenames)
    return len(files)

def datetimeToStrTime(dateTimeVal, strFormat=DEFAULT_DICOM_DATE_FORMAT):
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


