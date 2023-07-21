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


def countFilesInDir(dirName):
    files = []
    if os.path.isdir(dirName):
        for path, dirs, filenames in os.walk(dirName):  # @UnusedVariable
            files.extend(filenames)
    return len(files)

def datetimeToStrTime(dateTimeVal):
    return dateTimeVal.strftime("%H%M%S")