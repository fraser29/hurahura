import os


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


def countFilesInDir(dirName):
    files = []
    if os.path.isdir(dirName):
        for path, dirs, filenames in os.walk(dirName):  # @UnusedVariable
            files.extend(filenames)
    return len(files)

def datetimeToStrTime(dateTimeVal, strFormat=DEFAULT_DICOM_DATE_FORMAT):
    return dateTimeVal.strftime(DEFAULT_DICOM_DATE_FORMAT)