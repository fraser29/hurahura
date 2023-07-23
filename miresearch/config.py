# -*- coding: utf-8 -*-

import configparser
from collections import OrderedDict
import os

thisConfFileName = 'miresearch.conf'
rootDir = os.path.abspath(os.path.dirname(__file__))

config = configparser.ConfigParser(dict_type=OrderedDict)

# Will check for and read all below files with increasing precedence
all_config_files = [os.path.join(rootDir,thisConfFileName), 
                    os.path.join(os.path.expanduser("~"),thisConfFileName),
                    os.path.join(os.path.expanduser("~"),'.'+thisConfFileName), 
                    os.path.join(os.path.expanduser("~"), '.config',thisConfFileName),
                    os.environ.get("MIRESEARCH_CONF", '')]

config.read(all_config_files)

environment = config.get("app", "environment")
DEBUG = config.get("app", "debug")

