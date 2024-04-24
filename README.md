# miresearch
Organisation and automation tools for medical imaging research data

## Installation: 

```bash
pip install imaging-research
```
Note: pypi reported naming conflicts for miresearch

> [!IMPORTANT]  
> This package is currently undergoing frequent development and testing. Please check back regularly for version updates.

## About

This is a collection of classes for following OOP principles for organisation of research data for medical imaging research studies. 

It takes advantage of the dicom standard and the package [spydcmtk](https://github.com/fraser29/spydcmtk) for automating and generalising many typical steps with the intention of making the researcher's life easier. 

This package may be easily adapted and expanded upon for a high level control over your research data. Or, it may be used as is for basic structure and organisation of data and automation of common tasks. 

> [!NOTE]  
> Version 0.1.0 release: Greater flexibility in subject ID naming and stability improvements to miresearch_watchdog.


## Class structure

**AbstractSubject**  class is top level class taking inputs:
- *subjectNumber* : an integer
- *dataRoot* : the root directory where subjects to be stored             
- *subjectPrefix* : a prefix to be combined with *subjectNumber* for naming each subject
    - Optional: will be guessed from subjects already present in *dataRoot* if not given. 
- *DIRECTORY_STRUCTURE_TREE* : DirectoryStructureTree class to define directory structure for each subject directory (see wiki for construction shortcuts)
    - Optional: Defaults to **RAW** and **META** directories. 

This is the basic parent class containing fundamental methods for organisation and management. See  [miresearch docs](https://fraser29.github.io/miresearch/) for advanced usage, epsecially via inheritance and polymorphism. 

# Exposed commandline tool: miresearch

```bash

miresearch -h
usage: miresearch [-h] [-config CONFIGFILE] [-FORCE] [-QUIET] [-INFO] [-DEBUG] [-s [SUBJNLIST ...]] [-sf SUBJNLISTFILE] [-sR SUBJRANGE SUBJRANGE] [-y DATAROOT] [-sPrefix SUBJPREFIX] [-anonName ANONNAME]CODE
                  [-Load LOADPATH] [-LOAD_MULTI] [-LOAD_MULTI_FORCE] [-RunPost] [-SubjInfo] [-SummaryCSV SUMMARYCSV] [-WatchDirectory WATCHDIRECTORY]

options:
  -h, --help            show this help message and exit

Management Parameters:
  -config CONFIGFILE    Path to configuration file to use.
  -FORCE                force action - use with caution
  -QUIET                Suppress progress bars and logging to terminal
  -INFO                 Provide setup (configuration) info and exit.
  -DEBUG                Run in DEBUG mode (save intermediate steps, increase log output)

Subject Definition:
  -s [SUBJNLIST ...]    Subject number
  -sf SUBJNLISTFILE     Subject numbers in file
  -sR SUBJRANGE SUBJRANGE
                        Subject range
  -y DATAROOT           Path of root data directory (where subjects are stored) [default None -> may be set in config file]
  -sPrefix SUBJPREFIX   Subject prefix [default None -> will get from config file OR dataRoot]
  -anonName ANONNAME    Set to anonymise newly loaded subject. Set to true to use for WatchDirectory. [default None]

Actions:
  -Load LOADPATH        Path to load dicoms from (file / directory / tar / tar.gz / zip)
  -LOAD_MULTI           Combine with "Load": Load new subject for each subdirectory under loadPath
  -LOAD_MULTI_FORCE     Combine with "Load": Force to ignore studyUIDs and load new ID per subdirectory
  -RunPost              Run post load pipeline
  -SubjInfo             Print info for each subject
  -SummaryCSV SUMMARYCSV
                        Write summary CSV file (give output file name)
  -WatchDirectory WATCHDIRECTORY
                        Will watch given directory for new data and load as new study

```

# Configuration

miresearch uses a miresearch.conf file for configuration. 

By default miresearch.conf files are search for in the following locations: 

1. source_code_directory/miresearch.conf (file with default settings)
2. $HOME/miresearch.conf
3. $HOME/.miresearch.conf
4. $HOME/.config/miresearch.conf
5. Full file path defined at environment variable: "MIRESEARCH_CONF"
6. Full path passed as commandline argument to `miresearch`

Files are read in the above order with each subsequent variable present overwritting any previously defined. 
For information on files found and variables used run:

`miresearch -INFO` 

# Documentation

For full documentation see [miresearch docs](https://fraser29.github.io/miresearch/)