.. _anonymisation:

Anonymisation
===============

---------------------------------------------------------
*Anonymisation of DICOM data in hurahura*
---------------------------------------------------------

Anonymisation of DICOM data in hurahura is achieved via the use of the *spydcmtk* library.

See: https://pypi.org/project/spydcmtk/ for more information on the spydcmtk library.

Anonymisation can be controlled by the configuration file or by the command line.

In the configuration file *anon_level* may be set to:
- **NONE**: No anonymisation is performed.
- **SOFT**: *Appropriate for in-house use*
    - The patient name is anonymised in DICOM files by replacing with an empty string. 
    - The PatientID is retained in META file and DICOM files.
    - The PatientName is replaced with an empty string in DICOM files.
    - All PN tags are replaced with an empty string or "anonymous" as appropriate.
    - Date of birth, institution and adresses are anonymised. 
    - In the Meta file the "NAME" (surname) and "FIRST_NAMES" tags are encoded with the subject ID.
        - This is recoverable if necessary - see :ref:`mi_subject` AbstractSubject.getName() and AbstractSubject.getName_FirstNames()
    - The Age is retained in the META file.
- **HARD**: *Appropriate for public release / sharing*
    - The patient name and ID are anonymised in DICOM files by replacing with an empty string.
    - In the Meta file the "NAME" (surname) and "FIRST_NAMES" tags are set to encoded versions of "Name-Unknown" and "FirstNames-Unknown".
        -  :ref:`mi_subject` AbstractSubject.getName() and AbstractSubject.getName_FirstNames() will return "Name-Unknown" and "FirstNames-Unknown" respectively.
    - The Age is retained in the META file.

Alternatively, the anonymisation level can be specified for each subject via the command line:

.. code-block:: bash
    hurahura -s N -anon SOFT

    # Anonymise subject N with name "SubjABC" using the SOFT anonymisation level.   

