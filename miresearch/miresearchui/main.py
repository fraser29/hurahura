#!/usr/bin/env python3

import os
from datetime import datetime

from nicegui import ui
from local_directory_picker import local_directory_picker
from content.general import subject_page

# PYTHONPATH=/home/fraser/DEV/miresearch/
from miresearch import mi_subject
from miresearch.mi_config import MIResearch_config
DEBUG = True

# TODO best here that I set from a config file - i.e. give dict - name - then 
# hardcoded_presets = {"ProjA": {"data_root_dir": "/home/fraser/WORK/MI_DATA/tmpTestSubjs2",
#                                 "class_obj": mi_subject.AbstractSubject,
#                                 "subject_prefix": None,
#                                 "anon_level": None}, 
#                     "ProjB": {"conf_file": "miresearchui/projB.conf"},
#                     "ProjC": {"conf_file": "miresearchui/projC.conf"}}
hardcoded_presets = {"ProjC": {"conf_file": "/home/fraser/MSK.conf"}}


def get_index_of_field_open(data):
    for index, dictionary in enumerate(data):
        if dictionary.get('field') == 'open':
            return index
    return -1  # Return -1 if no dictionary with field 'open' is found



def _definePresetFromConfigfile(configFile):
    MIResearch_config.runconfigParser(configFile)
    return {"data_root_dir": MIResearch_config.data_root_dir, 
            "class_obj": MIResearch_config.class_obj,
            "subject_prefix": MIResearch_config.subject_prefix,
            "anon_level": MIResearch_config.anon_level}


class miresearch_ui():

    def __init__(self, dataRoot=None) -> None:
        self.dataRoot = dataRoot
        self.subjectList = []
        self.tableRows = []

        self.presetDict = {}
        self.setPresets(hardcoded_presets)

        self.tableCols = [
            {'field': 'subjID', 'sortable': True, 'checkboxSelection': True, 'filter': 'agTextColumnFilter', 'filterParams': {'filterOptions': ['contains', 'notContains']}},
            {'field': 'name', 'editable': True, 'filter': 'agTextColumnFilter', 'sortable': True, 'filterParams': {'filterOptions': ['contains', 'notContains', 'startsWith']}},
            {'field': 'DOS', 'sortable': True, 'filter': 'agDateColumnFilter', 'filterParams': {
                'comparator': 'function(filterLocalDateAtMidnight, cellValue) { '
                              'if (!cellValue) return false; '
                              'var dateParts = cellValue.split(""); '
                              'var cellDate = new Date(dateParts[0] + dateParts[1] + dateParts[2] + dateParts[3], '
                              'dateParts[4] + dateParts[5] - 1, '
                              'dateParts[6] + dateParts[7]); '
                              'return cellDate <= filterLocalDateAtMidnight; '
                              '}',
                'browserDatePicker': True,
            }},
            {'field': 'StudyID', 'sortable': True, 'filter': 'agNumberColumnFilter', 'filterParams': {'filterOptions': ['equals', 'notEqual', 'lessThan', 'lessThanOrEqual', 'greaterThan', 'greaterThanOrEqual', 'inRange']}},
            {'field': 'age', 'sortable': True, 'filter': 'agNumberColumnFilter', 'filterParams': {'filterOptions': ['inRange', 'lessThan', 'greaterThan',]}},
            {'field': 'levelCompleted', 'sortable': True, 'filter': 'agNumberColumnFilter', 'filterParams': {'filterOptions': ['lessThan', 'greaterThan',]}},
            
            {'field': 'open'} # 
        ]
        self.aggrid = None
        self.page = None  # Add this to store the page reference


    def setUpAndRun(self):        
        with ui.row():
            ui.button('Set subjects by directory', on_click=self.pick_file, icon='folder')
            for iProjName in self.presetDict.keys():
                print(f"Setting up button for {iProjName}")
                ui.button(iProjName, on_click=lambda proj=iProjName: self.setSubjectListFromPreset(proj))

        myhtml_column = get_index_of_field_open(self.tableCols)
        self.aggrid = ui.aggrid({
                        'columnDefs': self.tableCols,
                        'rowData': self.tableRows,
                        'rowSelection': 'multiple',
                        'stopEditingWhenCellsLoseFocus': True,
                        "pagination" : "true",
                        "paginationAutoPageSize" : "true",
                            }, 
                            html_columns=[myhtml_column])
        # with ui.row():
        #     ui.button('Run A', on_click=self.runA, icon='gear')
        #     ui.button('Run B', on_click=self.runA, icon='gear')
        ui.run()


    def setPresets(self, presetDict):
        for iName in presetDict.keys():
            if "conf_file" in presetDict[iName].keys():
                self.presetDict[iName] = _definePresetFromConfigfile(presetDict[iName]['conf_file'])
            else:
                self.presetDict[iName] = presetDict[iName]


    async def pick_file(self) -> None:
        try:
            result = await local_directory_picker('~', upper_limit=None, multiple=False)
            if DEBUG:
                print(f"Picked directory: {result}")
            if (result is None) or (len(result) == 0):
                return
            choosenDir = result[0]
            self.setSubjectListFromLocalDirectory(choosenDir)
        except Exception as e:
            print(f"Error in directory picker: {e}")
            ui.notify(f"Error selecting directory: {str(e)}", type='error')


    # async def runA(self) ->None:
    #     res = await self.aggrid.get_selected_rows()
    #     print(res)
    #     return True
    

    # async def runB(self) ->None:
    #     return True


    def setSubjectListFromPreset(self, projectName):
        print(f"Setting subject list from preset {projectName}")
        if projectName not in self.presetDict.keys():
            return
        self.setSubjectListFromLocalDirectory(localDirectory=self.presetDict[projectName].get("data_root_dir", "None"), 
                                              subject_prefix=self.presetDict[projectName].get("subject_prefix", None),  
                                              SubjClass=self.presetDict[projectName].get("class_obj", mi_subject.AbstractSubject), )
        


    def setSubjectListFromLocalDirectory(self, localDirectory, subject_prefix=None, SubjClass=mi_subject.AbstractSubject):
        if SubjClass is None:
            SubjClass = mi_subject.AbstractSubject
        if os.path.isdir(localDirectory):
            self.dataRoot = localDirectory
            self.subjectList = mi_subject.SubjectList.setByDirectory(self.dataRoot, 
                                                                     subjectPrefix=subject_prefix,
                                                                     SubjClass=SubjClass)
        if DEBUG:
            print(f"Have {len(self.subjectList)} subjects (should be {len(os.listdir(self.dataRoot))})")
        self.updateTable()


    def updateTable(self):
        self.clearTable()
        if DEBUG:
            print(self.aggrid.options['rowData'])
            print(f"Have {len(self.subjectList)} subjects - building table")
        c0 = 0
        for isubj in self.subjectList:
            c0 += 1
            self.tableRows.append({'subjID': isubj.subjID, 
                            'name': isubj.getName(), 
                            'DOS': isubj.getStudyDate(),  
                            'StudyID': isubj.getStudyID(),
                            'age': isubj.getAge(), 
                            'levelCompleted': isubj.getLevelCompleted(),
                            'open': f"<a href=subject_page/{isubj.subjID}?dataRoot={self.dataRoot}>View {isubj.subjID} </a>"})
                            # Below does not work as not JSON serilizable 
                            # 'open': ui.link(f"View {isubj.subjID}", f"subject_page/{isubj.subjID}?dataRoot={self.dataRoot}")}) 
        self.aggrid.options['rowData'] = self.tableRows
        self.aggrid.update()
        if DEBUG:
            print(f'Done - {len(self.tableRows)}')


    def clearTable(self):
        # self.subjectList = []
        tRowCopy = self.tableRows.copy()
        for i in tRowCopy:
            self.tableRows.remove(i)
        self.aggrid.update()


def run():
    miui = miresearch_ui()
    miui.setUpAndRun()



if __name__ in {"__main__", "__mp_main__"}:
    run()

