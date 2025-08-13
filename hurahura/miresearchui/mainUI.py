#!/usr/bin/env python3

import os
import sys
import logging
import shutil
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

print(f"=== Starting mainUI.py === DEBUG: {MIResearch_config.DEBUG}")  

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if MIResearch_config.DEBUG:
    logger.setLevel(logging.DEBUG)

# Remove all existing handlers first
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
if MIResearch_config.DEBUG:
    console_handler.setLevel(logging.DEBUG)

# Create formatter
formatter = logging.Formatter('%(asctime)s | %(levelname)-7s | %(name)s | %(message)s', datefmt='%d-%b-%y %H:%M:%S')
console_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(console_handler)


# ==========================================================================================

# ==========================================================================================
# ==========================================================================================
# MAIN CLASS 
# ==========================================================================================
class MIResearchUI():

    def __init__(self, port=8080) -> None:
        self.dataRoot = MIResearch_config.data_root_dir
        self.subjectList = []
        self.SubjClass = MIResearch_config.class_obj
        self.subject_prefix = MIResearch_config.subject_prefix
        self.tableRows = []
        self.port = port
        self.tableCols = [
            {'field': 'subjID', 'sortable': True, 'checkboxSelection': True, 'multiSelect': True, 'filter': 'agTextColumnFilter', 'filterParams': {'filterOptions': ['contains', 'notContains']}},
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
            {'field': 'age', 'sortable': True, 'filter': 'agNumberColumnFilter', 'filterParams': {'filterOptions': ['inRange', 'lessThan', 'greaterThan',]}, 'valueFormatter': 'value.toFixed(2)'},
            {'field': 'status', 'sortable': True, 'filter': 'agTextColumnFilter', 'filterParams': {'filterOptions': ['contains', 'notContains']}},
            
            {'field': 'open'} # 
        ]
        self.aggrid = None
        self.page = None  # Add this to store the page reference

        miui_settings_page.initialize_settings_ui(self)

    # ========================================================================================
    # SETUP AND RUN
    # ========================================================================================        
    def setUpAndRun(self):    
        logger.debug("Starting setUpAndRun")
        # Create a container for all UI elements
        with ui.column().classes('w-full h-full') as main_container:
            with ui.row().classes('w-full border'):
                ui.input(label='Data Root', value=self.dataRoot, on_change=self.updateDataRoot).classes('min-w-[32rem]')
                ui.input(label='Subject Prefix', value=self.subject_prefix, on_change=self.updateSubjectPrefix)
                ui.space()
                ui.button('', on_click=self.refresh, icon='refresh').classes('ml-auto')
                # ui.button('', on_click=self.show_settings_page, icon='settings').classes('ml-auto')

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
            logger.debug("Creating button row")
            with ui.row():
                ui.button('Load subject', on_click=self.load_subject, icon='upload')
                ui.button('Delete selected', on_click=self.delete_selected, icon='delete')
                ui.button('Shutdown', on_click=self.shutdown, icon='power_settings_new')
            
            # Footer
            with ui.row().classes('w-full bg-gray-100 border-t p-4 mt-8'):
                with ui.column().classes('w-full text-center'):
                    ui.label('hurahura - Medical Imaging Research Platform').classes('text-sm text-gray-600')
                    with ui.row().classes('w-full justify-center mt-2'):
                        ui.link('Documentation', 'https://fraser29.github.io/hurahura/').classes('text-xs text-blue-600 hover:text-blue-800 mx-2')
                        ui.link('GitHub', 'https://github.com/fraser29/hurahura').classes('text-xs text-blue-600 hover:text-blue-800 mx-2')
        
        logger.debug(f"Running UI on port {self.port}")
        self.setSubjectList()
        
        logger.debug(f"setUpAndRun completed, returning main_container")
        # Return the main container so it's displayed on the page
        return main_container

    
    def updateDataRoot(self, e):
        self.dataRoot = e.value
    
    def updateSubjectPrefix(self, e):
        self.subject_prefix = e.value
    
    
    def refresh(self):
        logger.info(f"Refreshing subject list for {self.dataRoot} with prefix {self.subject_prefix}")
        self.setSubjectList()


    def shutdown(self):
        logger.info("Shutting down UI")
        app.shutdown()

    # ========================================================================================
    # SUBJECT LEVEL ACTIONS
    # ========================================================================================      
    async def load_subject(self) -> None:
        logger.debug("Init loading subject")
        try:
            # Simple directory picker without timeout
            picker = local_file_picker('~', upper_limit=None, multiple=False, DIR_ONLY=True)
            result = await picker
            logger.debug(f"Result: {result}")
            
            if (result is None) or (len(result) == 0):
                logger.debug("No directory chosen")
                return
            
            choosenDir = result[0]
            logger.info(f"Directory chosen: {choosenDir}")
            
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
                    logger.info(f"Loading subject from {choosenDir} to {self.dataRoot}")
                    await asyncio.to_thread(mi_subject.createNew_OrAddTo_Subject, choosenDir, self.dataRoot, self.SubjClass)
                    loading_notification.dismiss()
                    ui.notify(f"Loaded subject {self.SubjClass.subjID}", type='positive')
                    self.refresh()
                    
                except Exception as e:
                    loading_notification.dismiss()
                    ui.notify(f"Error loading subject: {str(e)}", type='error')
                    logger.error(f"Error loading subject: {e}")
            
            # Start background task
            ui.timer(0, lambda: background_load(), once=True)
            
        except Exception as e:
            logger.error(f"Error in directory picker: {e}")
            ui.notify(f"Error loading subject: {str(e)}", type='error')
        return True
    

    async def delete_selected(self):
        logger.info("Checking for selected subjects")
        selected_rows = await self.aggrid.get_selected_rows()
        subject_ids = [row.get('subjID', 'Unknown') for row in selected_rows]
        logger.info(f"Selected rows: {subject_ids}")
        
        if not selected_rows:
            ui.notify("No subjects selected for deletion", type='warning')
            return
            
        # Ask for confirmation
        count = len(selected_rows)
        subject_list = ', '.join(subject_ids[:3])  # Show first 3, add "..." if more
        if count > 3:
            subject_list += f" and {count - 3} more"
            
        message = f"Are you sure you want to delete {count} selected subject(s)?\n\nSubjects: {subject_list}"
        logger.debug(f"Run confirm dialog:")
        
        # Create and show the confirmation dialog
        dialog = ui.dialog()
        with dialog, ui.card():
            ui.label(message).classes('text-lg mb-4')
            with ui.row().classes('w-full justify-end'):
                ui.button('Cancel', on_click=dialog.close).props('outline')
                ui.button('Delete', on_click=lambda: self._confirm_delete(subject_ids, dialog)).classes('bg-red-500 hover:bg-red-600 text-white')
        
        # Open the dialog
        dialog.open()


    def _confirm_delete(self, subject_ids, dialog):
        """Handle the actual deletion after user confirmation"""
        logger.info(f"User confirmed deletion of {len(subject_ids)} subjects")
        dialog.close()
        try:
            for iSubjectID in subject_ids:
                logger.info(f"Deleting subject: {iSubjectID}")
                shutil.rmtree(os.path.join(self.dataRoot, iSubjectID))
            ui.notify(f"Deletion confirmed for {len(subject_ids)} subject(s)", type='positive')
            logger.debug(f"Run confirm dialog: done")
            self.refresh()
        except Exception as e:
            logger.error(f"Error during deletion: {e}")
            ui.notify(f"Error during deletion: {str(e)}", type='error')
    
    
    # ========================================================================================
    # SET SUBJECT LIST
    # ========================================================================================    
    def setSubjectList(self):
        logger.info(f"Setting subject list for {self.dataRoot} with prefix {self.subject_prefix}. Class: {self.SubjClass}")
        self.subjectList = mi_subject.SubjectList.setByDirectory(self.dataRoot, 
                                                                    subjectPrefix=self.subject_prefix,
                                                                    SubjClass=self.SubjClass)
        logger.info(f"Have {len(self.subjectList)} subjects ({len(os.listdir(self.dataRoot))} possible sub-directories)")
        self.updateTable()

    # ========================================================================================
    # UPDATE TABLE
    # ========================================================================================  
    def updateTable(self):
        self.clearTable()
        logger.info(f"Have {len(self.subjectList)} subjects - building table")
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
                            'status': isubj.getStatus(),
                            'open': f"<a href={addr}>View {isubj.subjID}</a>"})
        self.aggrid.options['rowData'] = self.tableRows
        self.aggrid.update()
        logger.debug(f'Done - update table - {len(self.tableRows)} rows')


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
    @ui.page('/miresearch', title='hurahura - Medical Imaging Research')
    def run():
        logger.debug("Page /miresearch accessed")
        global _global_ui_runner
        if _global_ui_runner is None:
            logger.error("UI not initialized")
            return ui.label("Error: UI not initialized")
        
        try:
            # Set up the UI when this page is accessed and return the UI elements
            result = _global_ui_runner.miui.setUpAndRun()
            logger.debug(f"UI setup completed")
            return result
        except Exception as e:
            logger.error(f"Error in UI setup: {e}")
            import traceback
            traceback.print_exc()
            # Return a simple error message if setup fails
            return ui.label(f"Error setting up UI: {e}")

    @staticmethod
    @ui.page('/')
    def home():
        logger.debug("Home page accessed, redirecting to miresearch")
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
    try:
        ui.run(port=miui.port, show=True, reload=False, favicon='🩻', title='hurahura')
    except KeyboardInterrupt:
        logger.info("MIUI shutdown requested by user")

if __name__ in {"__main__", "__mp_main__"}:
    # app.on_shutdown(miui_helpers.cleanup)
    if len(sys.argv) > 1:
        port = int(sys.argv[1]) 
    else:
        port = 8081
    logger.info(f"Starting MIRESEARCH UI on port {port}")
    runMIUI(port=port)

