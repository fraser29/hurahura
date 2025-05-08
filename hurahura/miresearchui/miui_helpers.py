#!/usr/bin/env python3

from urllib.parse import urlparse, parse_qs
import importlib
import asyncio
from hurahura import mi_subject
from hurahura.mi_config import MIResearch_config
DEBUG = True


# ==========================================================================================
# HELPER FUNCTIONS  
# ==========================================================================================

async def cleanup():
    # Clean up any remaining tasks, close any event loops
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    loop = asyncio.get_event_loop()
    if not loop.is_closed():
        loop.close()


def get_index_of_field_open(data):
    for index, dictionary in enumerate(data):
        if dictionary.get('field') == 'open':
            return index
    return -1  # Return -1 if no dictionary with field 'open' is found

def definePresetFromConfigfile(configFile):
    MIResearch_config.runConfigParser(configFile)
    return {"data_root_dir": MIResearch_config.data_root_dir, 
            "subject_class_name": MIResearch_config.subject_class_name,
            "subject_prefix": MIResearch_config.subject_prefix,
            "anon_level": MIResearch_config.anon_level}

def rowToSubjID_dataRoot_classPath(row):
    href = row['open']
    url = href.split('href=')[1].split('>')[0]
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    return {
        'subjID': row['subjID'],
        'dataRoot': params['dataRoot'][0],  # parse_qs returns lists, get first item
        'classPath': params['classPath'][0]
    }

def subjID_dataRoot_classPathTo_SubjObj(subjID, dataRoot, classPath):
    SubjClass = mi_subject.AbstractSubject
    if classPath:
        module_name, class_name = classPath.rsplit('.', 1)
        SubjClass = getattr(importlib.import_module(module_name), class_name)
    return SubjClass(subjID, dataRoot=dataRoot)