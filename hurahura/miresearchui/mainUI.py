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
from hurahura.mi_config import MIResearch_config


# ==========================================================================================

# ==========================================================================================
# ==========================================================================================
# MAIN CLASS 
# ==========================================================================================
class MIResearchUI():

    def __init__(self, port=8080) -> None:
        self.DEBUG = MIResearch_config.DEBUG
        self.dataRoot = MIResearch_config.data_root_dir
        self.subjectList = []
        self.SubjClass = mi_subject.get_configured_subject_class()
        self.subject_prefix = MIResearch_config.subject_prefix
        self.tableRows = []
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

    # ========================================================================================
    # SETUP AND RUN
    # ========================================================================================        
    def setUpAndRun(self):    
        if self.DEBUG:
            print(f"DEBUG: Starting setUpAndRun")
        # Create a container for all UI elements
        with ui.column().classes('w-full h-full') as main_container:
            if self.DEBUG:
                print(f"DEBUG: Created main container")
            with ui.row().classes('w-full border'):
                if self.DEBUG:
                    print(f"DEBUG: Creating input row")
                ui.input(label='Data Root', value=self.dataRoot, on_change=self.updateDataRoot)
                ui.input(label='Subject Prefix', value=self.subject_prefix, on_change=self.updateSubjectPrefix)
                ui.space()
                ui.button('', on_click=self.refresh, icon='refresh').classes('ml-auto')
                # ui.button('', on_click=self.show_settings_page, icon='settings').classes('ml-auto')

            myhtml_column = miui_helpers.get_index_of_field_open(self.tableCols)
            if self.DEBUG:
                print(f"DEBUG: Creating table row")
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
            if self.DEBUG:
                print(f"DEBUG: Creating button row")
            with ui.row():
                ui.button('Load subject', on_click=self.load_subject, icon='upload')
                ui.button('Shutdown', on_click=self.shutdown, icon='power_settings_new')
        
        if self.DEBUG:
            print(f"DEBUG: Running UI on port {self.port}. Debug mode is {self.DEBUG}")
        self.setSubjectList()
        
        if self.DEBUG:
            print(f"DEBUG: setUpAndRun completed, returning main_container: {main_container}")
        # Return the main container so it's displayed on the page
        return main_container

    
    def updateDataRoot(self, e):
        self.dataRoot = e.value
    
    def updateSubjectPrefix(self, e):
        self.subject_prefix = e.value
    
    
    def refresh(self):
        print(f"DEBUG: Refreshing subject list for {self.dataRoot} with prefix {self.subject_prefix}")
        if self.DEBUG:
            print(f"DEBUG: Refreshing subject list for {self.dataRoot} with prefix {self.subject_prefix}")
        self.setSubjectList()


    def shutdown(self):
        print(f"DEBUG: Shutting down UI")
        app.shutdown()

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
    def setSubjectList(self):
        if self.DEBUG:
            print(f"Setting subject list for {self.dataRoot} with prefix {self.subject_prefix}")
        self.subjectList = mi_subject.SubjectList.setByDirectory(self.dataRoot, 
                                                                    subjectPrefix=self.subject_prefix,
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
# Global instance to hold the UI configuration
_global_ui_runner = None

class UIRunner():
    def __init__(self, port=8081):
        self.miui = MIResearchUI(port=port)
        self.port = port
        # Store this instance globally so the page methods can access it
        global _global_ui_runner
        _global_ui_runner = self

    @staticmethod
    @ui.page('/miresearch')
    def run():
        print(f"DEBUG: Page /miresearch accessed")
        global _global_ui_runner
        if _global_ui_runner is None:
            return ui.label("Error: UI not initialized")
        
        try:
            # Set up the UI when this page is accessed and return the UI elements
            result = _global_ui_runner.miui.setUpAndRun()
            print(f"DEBUG: UI setup completed, returning: {result}")
            return result
        except Exception as e:
            print(f"DEBUG: Error in UI setup: {e}")
            import traceback
            traceback.print_exc()
            # Return a simple error message if setup fails
            return ui.label(f"Error setting up UI: {e}")

    @staticmethod
    @ui.page('/')
    def home():
        print(f"DEBUG: Home page accessed, redirecting to miresearch")
        # Redirect to the miresearch page
        ui.navigate.to('/miresearch')
        return ui.label("Redirecting to MIRESEARCH...")


# ==========================================================================================
# RUN THE UI
# ==========================================================================================    
def runMIUI(port=8081):
    # Create the UI instance
    miui = UIRunner(port=port)
    # Start the NiceGUI server
    ui.run(port=miui.port, show=True, reload=False)

if __name__ in {"__main__", "__mp_main__"}:
    # app.on_shutdown(miui_helpers.cleanup)
    if len(sys.argv) > 1:
        port = int(sys.argv[1]) 
    else:
        port = 8081
    runMIUI(port=port)

