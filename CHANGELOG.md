# Changelog

All notable changes to this project will be documented in this file.

## [0.1.25]
- Feature add - UI active - for web based user interface. #FIXME: _WORKING_

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

