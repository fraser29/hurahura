#!/usr/bin/env python3

import os
import sys
from urllib.parse import quote
from nicegui import ui, app
from ngawari import fIO
import asyncio  

from hurahura import mi_subject
from hurahura.miresearchui import miui_helpers
from hurahura.miresearchui.local_directory_picker import local_file_picker
from hurahura.miresearchui.subjectUI import subject_page
from hurahura.miresearchui import miui_settings_page

DEBUG = True

hardcoded_presets = {}

# ==========================================================================================

# ==========================================================================================
# ==========================================================================================
# MAIN CLASS 
# ==========================================================================================
class MIResearchUI():

    def __init__(self, dataRoot=None, port=8080) -> None:
        self.DEBUG = DEBUG
        self.dataRoot = dataRoot
        self.subjectList = []
        self.SubjClass = mi_subject.get_configured_subject_class()
        self.tableRows = []
        self.presetDict = {}
        self.setPresets(hardcoded_presets)
        self.port = port
        self.tableCols = [
            {'field': 'subjID', 'sortable': True, 'checkboxSelection': True, 'filter': 'agTextColumnFilter', 'filterParams': {'filterOptions': ['contains', 'notContains']}},
            {'field': 'name', 'editable': True, 
                'filter': 'agTextColumnFilter', 
                'sortable': True, 
                'filterParams': {'filterOptions': ['contains', 'notContains', 'startsWith']}},
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

        miui_settings_page.initialize_settings_ui(self)

    @property
    def miui_conf_file(self):
        miuiConfDir = os.path.expanduser('~/.config/miresearch')
        miuiConfFile = os.path.join(miuiConfDir, 'miresearchui.conf')
        if not os.path.isfile(miuiConfFile):
            os.makedirs(miuiConfDir, exist_ok=True)
            with open(miuiConfFile, 'w') as f:
                f.write("")
        return miuiConfFile


    @property   
    def miui_conf_file_contents(self):
        return fIO.parseFileToTagsDictionary(self.miui_conf_file)


    def _saveMIUI_ConfigFile(self, configFile):
        if not isinstance(configFile, list):
            configFile = [configFile]
        confContents = self.miui_conf_file_contents
        for iFile in configFile:
            confName = os.path.splitext(os.path.basename(iFile))[0]
            confContents[confName] = iFile
        fIO.writeDictionaryToFile(self.miui_conf_file, confContents)


    def setPresets(self, presetDict):
        for iName in presetDict.keys():
            if "conf_file" in presetDict[iName].keys():
                iConfFile = presetDict[iName]['conf_file']
                try:
                    self.presetDict[iName] = miui_helpers.definePresetFromConfigfile(iConfFile)
                except FileNotFoundError:
                    print(f"Unable to find file {iConfFile}")
                except ModuleNotFoundError as e:
                    print(f"Error loading {iConfFile}")
                    print(f"   {e}")
            else:
                self.presetDict[iName] = presetDict[iName]


    async def chooseConfig(self) -> None:
        try:
            result = await local_file_picker('~', upper_limit=None, multiple=False)
            if self.DEBUG:
                print(f"Picked config file: {result}")
            if (result is None) or (len(result) == 0):
                return
            configFile = result[0]
            self._saveMIUI_ConfigFile(configFile)
            self.setSubjectListFromConfigFile(configFile)
        except Exception as e:
            print(f"Error in directory picker: {e}")
            ui.notify(f"Error selecting directory: {str(e)}", type='error')

    # ========================================================================================
    # SETUP AND RUN
    # ========================================================================================        
    def setUpAndRun(self):    
        miui_conf_dict = self.miui_conf_file_contents
        miui_conf_keys = list(miui_conf_dict.keys())
        for iKey in miui_conf_keys:
            self.presetDict[iKey] = miui_helpers.definePresetFromConfigfile(miui_conf_dict[iKey])
            # try:
            #     self.presetDict[iKey] = miui_helpers.definePresetFromConfigfile(miui_conf_dict[iKey])
            # except FileNotFoundError:
            #     print(f"Unable to find file {miui_conf_dict[iKey]}")
            # except Exception as e:
            #     print(f"Error loading {miui_conf_dict[iKey]}")
        print(f"Have {len(self.presetDict)} preset(s)")
        with ui.row().classes('w-full border'):
            ui.button('Choose config file', on_click=self.chooseConfig, icon='folder')
            for iProjName in self.presetDict.keys():
                print(f"Setting up button for {iProjName}")
                ui.button(iProjName, on_click=lambda proj=iProjName: self.setSubjectListFromConfigFile(proj))
            ui.space()
            ui.button('', on_click=self.updateTable, icon='refresh').classes('ml-auto')
            ui.button('', on_click=self.show_settings_page, icon='settings').classes('ml-auto')

        myhtml_column = miui_helpers.get_index_of_field_open(self.tableCols)
        with ui.row().classes('w-full flex-grow border'):
            self.aggrid = ui.aggrid({
                        'columnDefs': self.tableCols,
                        'rowData': self.tableRows,
                        # 'rowSelection': 'multiple',
                        'stopEditingWhenCellsLoseFocus': True,
                        "pagination" : "true",
                        'domLayout': 'autoHeight',
                            }, 
                            html_columns=[myhtml_column]).classes('w-full h-full')
        with ui.row():
            ui.button('Load subject', on_click=self.load_subject, icon='upload')
            ui.button('Shutdown', on_click=app.shutdown, icon='power_settings_new')
        ui.run(port=int(self.port))

    # ========================================================================================
    # SUBJECT LEVEL ACTIONS
    # ========================================================================================      
    async def load_subject(self) -> None:
        try:
            # Simple directory picker without timeout
            result = await local_file_picker('~', upper_limit=None, multiple=False, DIR_ONLY=True)
            
            if (result is None) or (len(result) == 0):
                return
            
            choosenDir = result[0]
            
            # Create loading notification
            loading_notification = ui.notification(
                message='Loading subject...',
                type='ongoing',
                position='top',
                timeout=None  # Keep showing until we close it
            )
            

            # Run the long operation in background
            async def background_load():
                try:
                    await asyncio.to_thread(mi_subject.createNew_OrAddTo_Subject, choosenDir, self.dataRoot, self.SubjClass)
                    loading_notification.dismiss()
                    ui.notify(f"Loaded subject {self.SubjClass.subjID}", type='positive')
                    
                except Exception as e:
                    loading_notification.dismiss()
                    ui.notify(f"Error loading subject: {str(e)}", type='error')
                    if self.DEBUG:
                        print(f"Error loading subject: {e}")
            
            # Start background task
            ui.timer(0, lambda: background_load(), once=True)
            
        except Exception as e:
            if self.DEBUG:
                print(f"Error in directory picker: {e}")
            ui.notify(f"Error loading subject: {str(e)}", type='error')
        return True
    
    # ========================================================================================
    # SET SUBJECT LIST 
    # ========================================================================================    
    def setSubjectListFromConfigFile(self, projectName):
        """
        Set the subject list from a config file (either selected or remembered)
        """
        if self.DEBUG:
            print(f"Setting subject list from config file {projectName}")
        if os.path.isfile(projectName):
            iName = os.path.splitext(os.path.basename(projectName))[0]
            self.presetDict[iName] = miui_helpers.definePresetFromConfigfile(projectName)
            projectName = iName
        if projectName not in self.presetDict.keys():
            return
        subjClass = mi_subject.get_configured_subject_class(self.presetDict[projectName].get("subject_class_name", None))
        self.setSubjectListFromLocalDirectory(localDirectory=self.presetDict[projectName].get("data_root_dir", "None"), 
                                              subject_prefix=self.presetDict[projectName].get("subject_prefix", None),  
                                              SubjClass=subjClass)
        

    def setSubjectListFromLocalDirectory(self, localDirectory, subject_prefix=None, SubjClass=None):
        if SubjClass is None:
            SubjClass = mi_subject.get_configured_subject_class()
        self.SubjClass = SubjClass
        if os.path.isdir(localDirectory):
            self.dataRoot = localDirectory
            self.subjectList = mi_subject.SubjectList.setByDirectory(self.dataRoot, 
                                                                     subjectPrefix=subject_prefix,
                                                                     SubjClass=self.SubjClass)
            if self.DEBUG:
                print(f"Have {len(self.subjectList)} subjects (should be {len(os.listdir(self.dataRoot))})")
            self.updateTable()

    # ========================================================================================
    # UPDATE TABLE
    # ========================================================================================  
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

    # ========================================================================================
    # SETTINGS PAGE
    # ========================================================================================      
    def show_settings_page(self):
        ui.navigate.to('/miui_settings')


# ==========================================================================================
# ==========================================================================================
class UIRunner():
    def __init__(self, port=8081):
        self.miui = MIResearchUI(port=port)

    @ui.page('/miresearch')
    def run(self):
        self.miui.setUpAndRun()


# ==========================================================================================
# RUN THE UI
# ==========================================================================================    
def runMIUI(port=8081):
    # Create the UI instance
    miui = UIRunner(port=port)
    miui.run()

if __name__ in {"__main__", "__mp_main__"}:
    # app.on_shutdown(miui_helpers.cleanup)
    if len(sys.argv) > 1:
        port = int(sys.argv[1]) 
    else:
        port = 8081
    runMIUI(port=port)

