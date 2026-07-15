# -*- coding: utf-8 -*-

import configparser
import json
from collections import OrderedDict
import os
import importlib

miresearch_conf = 'miresearch.conf'
rootDir = os.path.abspath(os.path.dirname(__file__))



class _MIResearch_config():
    def __init__(self, ) -> None:
        

        self.config = configparser.ConfigParser(dict_type=OrderedDict)
        self.all_config_files = [os.path.join(rootDir,miresearch_conf), 
                            os.path.join(os.path.expanduser("~"),miresearch_conf),
                            os.path.join(os.path.expanduser("~"),'.'+miresearch_conf), 
                            os.path.join(os.path.expanduser("~"), '.config',miresearch_conf),
                            os.environ.get("MIRESEARCH_CONF", '')]

    def runConfigParser(self, extraConfFile=None):
        
        if extraConfFile is not None:
            if os.path.isfile(extraConfFile):
                self.all_config_files.append(extraConfFile)
            else:
                print(f"WARNING: {extraConfFile} passed as config file to read, but FileNotFound - skipping")

        self.config.read(self.all_config_files)

        self.DEBUG = self.config.getboolean("app", "debug", fallback=False)
        self._anon_level = self.config.get("app", "anon_level", fallback='NONE')
        self._data_root_dir = ""
        self.data_root_dir = self.config.get("app", "data_root_dir", fallback="")
        self._subject_prefix = ""
        self.subject_prefix = self.config.get("app", "subject_prefix", fallback="")
        self.stable_directory_age_sec = self.config.getint("app", "stable_directory_age_sec", fallback=60)
        self.default_pad_zeros = self.config.getint("app", "default_pad_zeros", fallback=6)
        self.directory_structure = json.loads(self.config.get("app", "directories"))

        ## All parameters: 
        self.params = {}
        for section in self.config.sections():
            if section.lower() == 'parameters':
                self.params[section] = {}
                for option in self.config.options(section):
                    self.params[section][option] = self.config.get(section, option)

        self.subject_class_name = self.config.get("app", "class_path", fallback=None) 
        self.class_obj = self.config.get("app", "class_path", fallback=None)

        self.database_enabled = self.config.getboolean(
            "database", "enabled", fallback=False
        )
        self._database_path = self.config.get("database", "db_path", fallback="")
        self.database_sync_on_meta_write = self.config.getboolean(
            "database", "sync_on_meta_write", fallback=True
        )
        from hurahura.mi_database import DatabaseConfig
        self.database_field_config = DatabaseConfig.from_parser(self.config)


    def _resolve_optional_path(self, value: str):
        if not value or not str(value).strip():
            return None
        value = str(value).strip()
        if value.startswith("~"):
            value = os.path.expanduser(value)
        return os.path.abspath(value)

    @property
    def database_path(self):
        """SQLite file path; default is hurahura.db in the data root."""
        if self._database_path and len(self._database_path.strip()):
            path = self._database_path.strip()
            if path.startswith("~"):
                path = os.path.expanduser(path)
            return os.path.abspath(path)
        return os.path.join(self.data_root_dir, "hurahura.db")

    @property
    def data_root_dir(self):
        """Function to return data root from configuration. 

        Returns:
            str: Path to data root - found from config
        """
        if len(self._data_root_dir) == 0:
            raise ValueError(f"data_root_dir is not set in config file")
        return self._data_root_dir
    

    @data_root_dir.setter
    def data_root_dir(self, value):
        if value.startswith('~'):
            value = os.path.expanduser(value)
        self._data_root_dir = str(os.path.abspath(value))


    @property
    def subject_prefix(self):
        """Function to return subject prefix from configuration. 

        Returns:
            str: subjPrefix - found from config
        """
        if len(self._subject_prefix) == 0:
            return None
        return self._subject_prefix


    @subject_prefix.setter
    def subject_prefix(self, value):
        self._subject_prefix = str(value)


    @property
    def anon_level(self):
        if (len(self._anon_level) == 0) or (self._anon_level == 'NONE'):
            return None
        return self._anon_level
    
    @anon_level.setter
    def anon_level(self, value):
        if value is None:
            value = 'NONE'
        self._anon_level = str(value)

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
MIResearch_config.runConfigParser()