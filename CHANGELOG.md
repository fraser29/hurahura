# Changelog

All notable changes to this project will be documented in this file.


## [0.2.4]
- Bug fix - timeToDatetime - force strings for dateStr and timeStr. 

## [0.2.3]
- Feature add - getStartTime_EndTimeOfExam now returns datetime objects if RETURN_DATETIME is True.
- Utils function timeToDatetime now takes (optional) dateStr as an argument to return true datetime (not just time).

## [0.2.2]
- Feature add - Overview command line option to print quick overview of DB and all subjects
- Feature add - if negative subject number is given, get last N subjects. 
- Feature add - UI improvements and optimisations. 
- Bug fix - Series number in UI now shows number of images in series. 
- Bug fix - Error handling in UI now shows error message. 
- Feature add - Structure to build true (sqlite) database of subjects and series. (optional)

## [0.2.1]
- Update dependencies for spydmtk and ngawari to fix some DICOM to VTI issues (esp. with 3D DICOM)
- Bug fix in get series directory by description string - now returns None if no series is found.

## [0.1.33]
- Feature add: rsyncToOtherDataroot now uses --whole-file option to avoid potential cross-filesystem bugs.  

## [0.1.32]
- Bug fix: rsyncToOtherDataroot now uses --inplace option to avoid potential cross-filesystem bugs.  

## [0.1.30]
- Feature add: Edge case error catch on subjList creatation, if sub-class of AbstractSubject uses a suffix. 

## [0.1.29]
- Feature add: Improved error reporting from subclass failures. 

## [0.1.28]
- Bug fix: Edge case of default subject class given as "" rather than None. Or class object rather than module path defined. 

## [0.1.27]
- Feature add - meta cahcing for faster lookup in SubjectList operations. 
- UI - improvements and optimisations. 

## [0.1.26]
- Feature add - UI dynamic loading of subject for current page. 

## [0.1.25]
- Feature add - UI active - for web based user interface.

## [0.1.24]
- Feature add - for watcher - if encounter error - move watched data to "Error" directory

## [0.1.23]
### Fixed
- Bug fix on conf class definition

## [0.1.21]
### Added
- added age to meta file. Set at first request or upon anonymisation.

## [0.1.19]
### Fixed
- minor error on logging in debug mode. 

## [0.1.18]
### Fixed
- minor error catching on edge cases. 

## [0.1.17]
### Fixed 
- circular import bug fixed that can occur if SubjClass defined in conf file and read by environment variable


## [0.1.16]
### Fixed
- minor bugs occuring in edge cases. 

## [0.1.2] - 2025-02-11
### Added
- refactor miresearch (in pip as imaging-miresearch) to package named hurahura 

## [0.1.12] - 2025-04-15
### Added
- small bug fix - check if input is a string or Path

## [0.1.15] - 2025-04-15
### Removed
- removed anonymisation from watchdog
- catch NotADirectoryError when tar or zip files are deleted by watchdog. 

