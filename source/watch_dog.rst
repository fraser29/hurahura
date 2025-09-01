.. _watch_dog:

Watch Dog
===============

The watch dog is a tool that allows you to automate the loading of subjects from an "*INCOMING*" directory. 

This is best set up as a service and run in the background. 

.. code-block:: bash

    # Example service file. 
    [Unit]
    Description=My mi_watcher Service
    After=network.target

    [Service]
    Type=simple
    ExecStart=hurahura -config /path/to/myconf.conf -WatchDirectory /path/to/incoming
    Restart=on-failure

    [Install]
    WantedBy=multi-user.target

See: :ref:`https://fraser29.github.io/autorthanc/` for a DICOM SERVER with auto-download options that work nicely with the watch dog. 