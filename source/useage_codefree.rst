.. _useage_codefree:

Useage_codefree
===============

---------------------------------------------------------
*Code free use of hurahura*
---------------------------------------------------------

A number of primary features are available in hurahura that allows one to achieve full control of their data as well as enjoy the benefits of automation of various typical data management steps. 

execute hurahura -h to see all options. 

Customisation can be achieved via generating a custom conf file. 

A template conf file is below: 

.. code-block:: ini

    # DO NOT USE QUOTES FOR STRING
    # BUT - FOR STRINGS IN LISTS - ALWAYS USE DOUBLE QUOTES - these will be json decoded

    [DEFAULT]
    debug=False

    # Choose: HARD, SOFT, NONE
    anon_level = NONE

    stable_directory_age_sec=60
    default_pad_zeros=6

    [app]
    data_root_dir=/path/to/data
    subject_prefix=MI 

    directories = [["RAW", "DICOM"], "META"]
    # Override DEFAULT parameters here


    [parameters]
    # Add application specific parameters here

As shown above simple perminant changes can be made to the conf file. The reduces commandline inputs. 

The confi file may be provided as a commandline argument. 

.. code-block:: bash

    # List all conf variables and their values. 

    hurahura -c myconf.conf -INFO


Or may be defined by the MIRESEARCH_CONF environment variable. 

.. code-block:: bash

    # Set the MIRESEARCH_CONF environment variable. 
    export MIRESEARCH_CONF=myconf.conf
    hurahura -INFO
    # Same output as above. 


-------

With such a setup one may perform the following actions:

.. code-block:: bash

    # Build an empty subject with ID = 1. 

    hurahura -config myconf.conf -Build -s 1

.. code-block:: bash

    # Build a subject from a directory of DICOMS (next number in line is used as the subject ID). 

    hurahura -config myconf.conf -Load /path/to/dicoms


.. code-block:: bash

    # Build multiple subjects from a directory of DICOMS (one subject per sub-directory). 

    hurahura -config myconf.conf -Load /path/to/multiple-directories-of-dicoms -LOAD_MULTI


.. code-block:: bash

    # Add non-dicom data to a subject (need to give subject ID). 

    hurahura -config myconf.conf -LoadOther /path/to/non-dicom-data -s 1


.. code-block:: bash

    # Query all our subjects (option -sA) for those examined on date 25th March 2024 (option -qDate)
    hurahura -config myconf.conf -qDate 20210325 -sA

    # Query subjects 200 to 500 (option -sR) for those examined on date 25th March 2024 (option -qDate)
    hurahura -config myconf.conf -qDate 20210325 -sR 200 501

    # Produce a summary of all data in csv format
    hurahura -config myconf.conf -sA -SummaryCSV mysummary.csv


.. code-block:: bash

    # To view all options and help. 

    hurahura -h



Use the watch dog to automate loading while watching an "*INCOMING*" directory. See: :ref:`watch_dog` . 

