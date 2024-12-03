#!/usr/bin/env python3

import os
from datetime import datetime
from urllib.parse import quote
from nicegui import ui
from local_directory_picker import local_directory_picker
from general import subject_page

from miresearch import mi_subject
from miresearch.miresearchui import miui_helpers

DEBUG = True

# TODO best here that I set from a config file - i.e. give dict - name - then 
# hardcoded_presets = {"ProjA": {"data_root_dir": "/home/fraser/WORK/MI_DATA/tmpTestSubjs2",
#                                 "class_obj": mi_subject.AbstractSubject,
#                                 "subject_prefix": None,
#                                 "anon_level": None}, 
#                     "ProjB": {"conf_file": "miresearchui/projB.conf"},
#                     "ProjC": {"conf_file": "miresearchui/projC.conf"}}
hardcoded_presets = {"TestRuru": {"conf_file": "/home/fraser/MSK.conf"},
                     "TestMoa": {"conf_file": "/home/fraser/DEV/miresearch/miresearch/miresearchui/projC.conf"}}


# ==========================================================================================

# ==========================================================================================
# ==========================================================================================
# MAIN CLASS 
# ==========================================================================================
class miresearch_ui():

    def __init__(self, dataRoot=None) -> None:
        self.DEBUG = DEBUG
        self.dataRoot = dataRoot
        self.subjectList = []
        self.SubjClass = mi_subject.AbstractSubject # This is default - updated if read from config
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
        with ui.row().classes('w-full border'):
            ui.button('Set subjects by directory', on_click=self.pick_file, icon='folder')
            for iProjName in self.presetDict.keys():
                print(f"Setting up button for {iProjName}")
                ui.button(iProjName, on_click=lambda proj=iProjName: self.setSubjectListFromPreset(proj))
            ui.space()
            ui.button('Settings', on_click=self.settings_page, icon='settings').classes('ml-auto')

        myhtml_column = miui_helpers.get_index_of_field_open(self.tableCols)
        with ui.row().classes('w-full flex-grow border'):
            self.aggrid = ui.aggrid({
                        'columnDefs': self.tableCols,
                        'rowData': self.tableRows,
                        'rowSelection': 'multiple',
                        'stopEditingWhenCellsLoseFocus': True,
                        "pagination" : "true",
                        'domLayout': 'autoHeight',
                            }, 
                            html_columns=[myhtml_column]).classes('w-full h-full')
        with ui.row():
            ui.button('Load subject', on_click=self.load_subject, icon='upload')
            ui.button('Anonymise', on_click=self.anonymise_subject, icon='person_off')
        ui.run()


    def setPresets(self, presetDict):
        for iName in presetDict.keys():
            if "conf_file" in presetDict[iName].keys():
                self.presetDict[iName] = miui_helpers.definePresetFromConfigfile(presetDict[iName]['conf_file'])
            else:
                self.presetDict[iName] = presetDict[iName]


    async def pick_file(self) -> None:
        try:
            result = await local_directory_picker('~', upper_limit=None, multiple=False)
            if self.DEBUG:
                print(f"Picked directory: {result}")
            if (result is None) or (len(result) == 0):
                return
            choosenDir = result[0]
            self.setSubjectListFromLocalDirectory(choosenDir)
        except Exception as e:
            print(f"Error in directory picker: {e}")
            ui.notify(f"Error selecting directory: {str(e)}", type='error')


    async def load_subject(self) -> None:
        try:
            result = await local_directory_picker('~', upper_limit=None, multiple=False)
            if self.DEBUG:
                print(f"Picked directory: {result}")
            if (result is None) or (len(result) == 0):
                return
            choosenDir = result[0]
            self.SubjClass.load_subject(choosenDir)
            ui.notify(f"Loaded subject {self.SubjClass.subjID}", type='positive')
        except Exception as e:
            if self.DEBUG:
                print(f"Error in directory picker: {e}")
            ui.notify(f"Error loading subject: {str(e)}", type='error')
        return True
    

    async def anonymise_subject(self) -> None:
        selectedSubjects = await self.aggrid.get_selected_rows()
        for iSubj in selectedSubjects:
            defDict = miui_helpers.rowToSubjID_dataRoot_classPath(iSubj)
            thisSubj = miui_helpers.subjID_dataRoot_classPathTo_SubjObj(defDict['subjID'], defDict['dataRoot'], defDict['classPath'])
            try:
                thisSubj.anonymise()
                ui.notify(f"Anonymised subject {thisSubj.subjID}", type='positive')
            except Exception as e:
                ui.notify(f"Error anonymising subject {thisSubj.subjID}: {str(e)}", type='error')
        return True


    def settings_page(self):
        pass

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
        self.SubjClass = SubjClass
        if os.path.isdir(localDirectory):
            self.dataRoot = localDirectory
            self.subjectList = mi_subject.SubjectList.setByDirectory(self.dataRoot, 
                                                                     subjectPrefix=subject_prefix,
                                                                     SubjClass=self.SubjClass)
            if self.DEBUG:
                print(f"Have {len(self.subjectList)} subjects (should be {len(os.listdir(self.dataRoot))})")
            self.updateTable()


    def updateTable(self):
        self.clearTable()
        if self.DEBUG:
            print(self.aggrid.options['rowData'])
            print(f"Have {len(self.subjectList)} subjects - building table")
        c0 = 0
        for isubj in self.subjectList:
            c0 += 1
            classPath = self.SubjClass.__module__ + '.' + self.SubjClass.__name__
            addr = f"subject_page/{isubj.subjID}?dataRoot={quote(self.dataRoot)}&classPath={quote(classPath)}"
            self.tableRows.append({'subjID': isubj.subjID, 
                            'name': isubj.getName(), 
                            'DOS': isubj.getStudyDate(),  
                            'StudyID': isubj.getStudyID(),
                            'age': isubj.getAge(), 
                            'levelCompleted': isubj.getLevelCompleted(),
                            'open': f"<a href={addr}>View {isubj.subjID}</a>"})
        self.aggrid.options['rowData'] = self.tableRows
        self.aggrid.update()
        if self.DEBUG:
            print(f'Done - {len(self.tableRows)}')


    def clearTable(self):
        # self.subjectList = []
        tRowCopy = self.tableRows.copy()
        for i in tRowCopy:
            self.tableRows.remove(i)
        self.aggrid.update()


@ui.page('/')
async def run():
    # Create the UI instance
    miui = miresearch_ui()
    miui.setUpAndRun()

if __name__ in {"__main__", "__mp_main__"}:
    ui.run()

