# -*- coding: utf-8 -*-

import configparser
import json
from collections import OrderedDict
import os
import importlib

thisConfFileName = 'miresearch.conf'
rootDir = os.path.abspath(os.path.dirname(__file__))



class _MIResearch_config():
    def __init__(self, ) -> None:
        

        self.config = configparser.ConfigParser(dict_type=OrderedDict)
        self.all_config_files = [os.path.join(rootDir,thisConfFileName), 
                            os.path.join(os.path.expanduser("~"),thisConfFileName),
                            os.path.join(os.path.expanduser("~"),'.'+thisConfFileName), 
                            os.path.join(os.path.expanduser("~"), '.config',thisConfFileName),
                            os.environ.get("MIRESEARCH_CONF", '')]

    def runconfigParser(self, extraConfFile=None):
        
        if extraConfFile is not None:
            if os.path.isfile(extraConfFile):
                self.all_config_files.append(extraConfFile)
            else:
                print(f"WARNING: {extraConfFile} passed as config file to read, but FileNotFound - skipping")

        self.config.read(self.all_config_files)

        self.DEBUG = self.config.getboolean("app", "debug", fallback=False)
        self._anon_level = self.config.get("app", "anon_level", fallback='NONE')
        self._data_root_dir = self.config.get("app", "data_root_dir", fallback="")
        self._subject_prefix = self.config.get("app", "subject_prefix", fallback="")
        self.stable_directory_age_sec = self.config.getint("app", "stable_directory_age_sec", fallback=60)
        self.directory_structure = json.loads(self.config.get("app", "directories"))

        self.class_obj = None
        class_path = self.config.get("app", "class_path", fallback=None)
        if class_path:
            module_name, class_name = class_path.rsplit('.', 1)
            module = importlib.import_module(module_name)
            self.class_obj = getattr(module, class_name)

        ## All parameters: 
        self.params = {}
        for section in self.config.sections():
            if section.lower() == 'parameters':
                self.params[section] = {}
                for option in self.config.options(section):
                    self.params[section][option] = self.config.get(section, option)

    @property
    def data_root_dir(self):
        """Function to return data root from configuration. 

        Returns:
            str: Path to data root - found from config
        """
        if len(self._data_root_dir) == 0:
            raise ValueError(f"data_root_dir is not set in config file")
        return self._data_root_dir

    @property
    def subject_prefix(self):
        """Function to return subject prefix from configuration. 

        Returns:
            str: subjPrefix - found from config
        """
        if len(self._subject_prefix) == 0:
            return None
        return self._subject_prefix

    @property
    def anon_level(self):
        if (len(self._anon_level) == 0) or (self._anon_level == 'NONE'):
            return None
        return self._anon_level

    def printInfo(self):
        print(" ----- MIResearch Configuration INFO -----")
        print('   Using configuration files found at: ')
        for iFile in self.all_config_files:
            if os.path.isfile(iFile):
                print(f"    {iFile}")
        print('')
        print('   Configuration settings:')
        attributes = vars(self)
        for attribute_name in sorted(attributes.keys()):
            if 'config' in attribute_name:
                continue
            print(f"   --  {attribute_name}: {attributes[attribute_name]}")


MIResearch_config = _MIResearch_config()
MIResearch_config.runconfigParser()