# hurahura - formerly miresearch

Organisation and automation tools for medical imaging research data

__hurahura__ is māori for "to investigate" or "to look around"

## Installation: 

```bash
pip install hurahura
# formerly: pip install imaging-research

```

## About

This is a collection of classes for following OOP principles for organisation of research data for medical imaging research studies. 

The intention is to provide a framework that will store imaging data on a "per __examination__" basis in a structured format. This structured format then permits simple interrogation, and automation.  

It takes advantage of the dicom standard and the package [spydcmtk](https://pypi.org/project/spydcmtk/) for automating and generalising many typical steps with the intention of making the researcher's life easier. 

This package may be easily adapted and expanded upon for a high level control over your research data. Or, it may be used as is for basic structure and organisation of data and automation of common tasks. 


## Class structure

**AbstractSubject**  class is top level class taking inputs:
- *subjectNumber* : an integer
- *dataRoot* : the root directory where subjects to be stored             
- *subjectPrefix* : a prefix to be combined with *subjectNumber* for naming each subject
    - Optional: will be guessed from subjects already present in *dataRoot* if not given. 
- *DIRECTORY_STRUCTURE_TREE* : DirectoryStructureTree class to define directory structure for each subject directory (see wiki for construction shortcuts)
    - Optional: Defaults to **RAW** and **META** directories. 

This is the basic parent class containing fundamental methods for organisation and management. See  [hurahura docs](https://fraser29.github.io/hurahura/) for advanced usage, epsecially via inheritance and polymorphism. 


## Configuration

hurahura uses a miresearch.conf file for configuration. 

By default miresearch.conf files are search for in the following locations: 

1. source_code_directory/miresearch.conf (file with default settings)
2. $HOME/miresearch.conf
3. $HOME/.miresearch.conf
4. $HOME/.config/miresearch.conf
5. Full file path defined at environment variable: "MIRESEARCH_CONF"
6. Full path passed as commandline argument to `hurahura`

Files are read in the above order with each subsequent variable present overwritting any previously defined. 
For information on files found and variables used run:

`hurahura -INFO` 

## File system watcher

hurahura can watch a directory for new subjects and load them into the system. This works nicely with [AUTORTHANC](https://github.com/fraser29/autorthanc)

```bash
hurahura -WatchDirectory /path/to/watch_directory
```

## UI

hurahura can be run with a UI for easy management of subjects and data. 

```bash
hurahura -UI
```

# Documentation

For full documentation see [hurahura docs](https://fraser29.github.io/hurahura/)