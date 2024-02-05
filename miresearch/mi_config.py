# -*- coding: utf-8 -*-

import configparser
import json
from collections import OrderedDict
import os

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

        self.environment = self.config.get("app", "environment")
        self.DEBUG = self.config.getboolean("app", "debug", fallback=False)
        self.data_root_dir = self.config.get("app", "data_root_dir")
        self.stable_directory_age_sec = self.config.getint("app", "stable_directory_age_sec")


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