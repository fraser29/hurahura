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
# from hurahura.miresearchui import miui_settings_page
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

    # Constants
    ROWS_PER_PAGE = 20

    def __init__(self, port=8080) -> None:
        self.dataRoot = MIResearch_config.data_root_dir
        self.subjectList = []
        self.SubjClass = MIResearch_config.class_obj
        self.subject_prefix = MIResearch_config.subject_prefix
        self.tableRows = []
        self.port = port
        # Add pagination cache
        self.pageCache = {}  # Cache for loaded pages
        self.currentPage = 1
        self.pageSize = self.ROWS_PER_PAGE
        self.totalSubjects = 0
        
        # Store references to UI elements for updates
        self.page_info_label = None
        self.page_count_label = None
        
        self.tableCols = [
            {'field': 'subjID', 'sortable': True, 'checkboxSelection': True, 'multiSelect': True, 'filter': 'agTextColumnFilter', 'filterParams': {'filterOptions': ['contains', 'notContains']}},
            {'field': 'name', 
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

            myhtml_column = miui_helpers.get_index_of_field_open(self.tableCols)
            with ui.row().classes('w-full flex-grow border'):
                self.aggrid = ui.aggrid({
                            'columnDefs': self.tableCols,
                            'rowData': [],  # Start with empty data
                            'rowSelection': 'multiple',
                            'stopEditingWhenCellsLoseFocus': True,
                            'domLayout': 'autoHeight'
                                }, 
                                html_columns=[myhtml_column]).classes('w-full h-full')
                

            logger.debug("Creating button row")
            with ui.row():
                ui.button('Load subject', on_click=self.load_subject, icon='upload')
                ui.button('Delete selected', on_click=self.delete_selected, icon='delete')
                ui.button('Shutdown', on_click=self.shutdown, icon='power_settings_new')
                
                # Add page navigation info
                with ui.row().classes('w-full justify-center mt-2'):
                    self.page_info_label = ui.label(f'Page {self.currentPage} of {(self.totalSubjects + self.pageSize - 1) // self.pageSize}').classes('text-sm text-gray-600')
                    self.page_count_label = ui.label(f'({self.totalSubjects} total subjects, {self.pageSize} per page)').classes('text-xs text-gray-500 ml-2')
                
                # Add page navigation controls
                with ui.row().classes('w-full justify-center mt-2'):
                    ui.button('First', on_click=self.first_page, icon='first_page').classes('mx-1')
                    ui.button('Previous', on_click=self.prev_page, icon='navigate_before').classes('mx-1')
                    self.page_goto_input = ui.input(label='Go to page', value=str(self.currentPage), on_change=self.go_to_page).classes('w-20 mx-2')
                    ui.button('Next', on_click=self.next_page, icon='navigate_next').classes('mx-1')
                    ui.button('Last', on_click=self.last_page, icon='last_page').classes('mx-1')
            
            # Footer
            with ui.row().classes('w-full bg-gray-100 border-t p-4 mt-8'):
                with ui.column().classes('w-full text-center'):
                    ui.label('hurahura - Medical Imaging Research Platform').classes('text-sm text-gray-600')
                    with ui.row().classes('w-full justify-center mt-2'):
                        ui.link('Documentation', 'https://fraser29.github.io/hurahura/').classes('text-xs text-blue-600 hover:text-blue-800 mx-2')
                        ui.link('GitHub', 'https://github.com/fraser29/hurahura').classes('text-xs text-blue-600 hover:text-blue-800 mx-2')
        
        logger.debug(f"setUpAndRun completed, returning main_container")
        
        # Load initial data immediately
        self.setSubjectList()
        
        # Ensure page display is updated after initial load
        self.update_page_display()
        
        # Return the main container so it's displayed on the page
        return main_container

    def addPageChangeHandler(self):
        """Add JavaScript handler for page changes"""
        # No longer needed since we're not using aggrid pagination
        pass

    # ========================================================================================
    def updateDataRoot(self, e):
        self.dataRoot = e.value
    
    def updateSubjectPrefix(self, e):
        self.subject_prefix = e.value
    
    
    def refresh(self):
        logger.info(f"Refreshing subject list for {self.dataRoot} with prefix {self.subject_prefix}")
        # Clear cache and reload
        self.pageCache.clear()
        self.currentPage = 1
        self.setSubjectList()
        self.update_page_display()


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
        # Only get the directory listing, don't load all subjects
        self.subjectList = mi_subject.SubjectList.setByDirectory(self.dataRoot, 
                                                                    subjectPrefix=self.subject_prefix,
                                                                    SubjClass=self.SubjClass)
        self.totalSubjects = len(self.subjectList)
        logger.info(f"Found {self.totalSubjects} subjects ({len(os.listdir(self.dataRoot))} possible sub-directories)")
        
        # Debug: show what we found
        if self.totalSubjects == 0:
            logger.warning("No subjects found!")
        
        # Load first page
        self.loadPage(1)
        self.updateTable()
        self.update_page_display()


    def loadPage(self, page_num):
        """Load a specific page of data, with caching"""
        if page_num in self.pageCache:
            logger.debug(f"Page {page_num} found in cache")
            return self.pageCache[page_num]
        
        logger.info(f"Loading page {page_num} from disk (subjects {((page_num - 1) * self.pageSize) + 1}-{min(page_num * self.pageSize, self.totalSubjects)})")
        
        # Check if we have any subjects
        if not self.subjectList:
            logger.warning("No subjects available to load")
            self.pageCache[page_num] = []
            return []
        
        start_idx = (page_num - 1) * self.pageSize
        end_idx = start_idx + self.pageSize
        
        # Get subjects for this page
        page_subjects = self.subjectList[start_idx:end_idx]
        page_data = []
        
        for isubj in page_subjects:
            meta = isubj.getMetaDict()
            classPath = self.SubjClass.__module__ + '.' + self.SubjClass.__name__
            addr = f"subject_page/{isubj.subjID}?dataRoot={quote(self.dataRoot)}&classPath={quote(classPath)}"
            page_data.append({
                'subjID': isubj.subjID, 
                'name': meta.get('NAME', 'Unknown'),
                'DOS': meta.get('StudyDate', 'Unknown'),
                'StudyID': meta.get('StudyID', 'Unknown'),
                'age': meta.get('Age', 'Unknown'),
                'status': isubj.getStatus(),
                'open': f"<a href={addr}>View {isubj.subjID}</a>"
            })
        
        # Cache this page
        self.pageCache[page_num] = page_data
        logger.debug(f"Cached page {page_num} with {len(page_data)} rows")
        # Keep cache size manageable (keep current page + adjacent pages)
        self._cleanupCache(page_num)
        return page_data

    def getPaginationStats(self):
        """Get current pagination statistics for debugging"""
        total_pages = (self.totalSubjects + self.pageSize - 1) // self.pageSize
        cached_pages = list(self.pageCache.keys())
        return {
            'total_subjects': self.totalSubjects,
            'total_pages': total_pages,
            'current_page': self.currentPage,
            'page_size': self.pageSize,
            'cached_pages': cached_pages,
            'cache_size': len(self.pageCache)
        }

    def _cleanupCache(self, current_page):
        """Keep only current page and adjacent pages in cache"""
        pages_to_keep = {current_page, current_page - 1, current_page + 1}
        pages_to_remove = [p for p in self.pageCache.keys() if p not in pages_to_keep]
        
        for page in pages_to_remove:
            if page > 0:  # Don't remove page 0
                del self.pageCache[page]
                logger.debug(f"Removed page {page} from cache")

    def onPageChanged(self, new_page):
        """Handle page changes from the grid"""
        logger.info(f"Page changed to {new_page}")
        self.currentPage = new_page
        
        # Load the new page if not in cache
        if new_page not in self.pageCache:
            self.loadPage(new_page)
        
        # Update the table
        self.updateTable()

    # ========================================================================================
    # UPDATE TABLE
    # ======================================================================================== 
    def updateTable(self):
        """Update table with current page data"""
        # If no page cache exists yet, load the first page
        if not self.pageCache:
            self.loadPage(1)
        
        current_page_data = self.pageCache.get(self.currentPage, [])
        if not current_page_data:
            logger.warning(f"No data found for page {self.currentPage}")
            return
            
        # Update the grid with the current page data
        logger.info(f"Updating table with {len(current_page_data)} rows for page {self.currentPage}")
        
        # Use the proper aggrid update method - modify options and call update()
        self.aggrid.options['rowData'] = current_page_data
        self.aggrid.update()
        
        logger.debug(f'Updated table with {len(current_page_data)} rows from page {self.currentPage}')
        
        # If still no data, show a fallback message
        if not current_page_data and self.totalSubjects > 0:
            logger.warning("No data displayed despite having subjects. Adding fallback data.")
            # Add some fallback data to see if the grid is working
            fallback_data = [{'subjID': 'DEBUG', 'name': 'Debug Mode', 'DOS': 'N/A', 'StudyID': 'N/A', 'age': 'N/A', 'status': 'Debug', 'open': 'Debug Link'}]
            self.aggrid.options['rowData'] = fallback_data
            self.aggrid.update()
            logger.info("Added fallback debug data to verify grid functionality")


    def clearTable(self):
        self.tableRows = []
        self.pageCache.clear()
        self.currentPage = 1
        self.aggrid.options['rowData'] = []
        self.aggrid.update()


    def next_page(self):
        """Navigate to the next page"""
        total_pages = (self.totalSubjects + self.pageSize - 1) // self.pageSize
        if self.currentPage < total_pages:
            self.currentPage += 1
            self.loadPage(self.currentPage)
            self.updateTable()
            self.update_page_display()

    def prev_page(self):
        """Navigate to the previous page"""
        if self.currentPage > 1:
            self.currentPage -= 1
            self.loadPage(self.currentPage)
            self.updateTable()
            self.update_page_display()

    def first_page(self):
        """Navigate to the first page"""
        if self.currentPage > 1:
            self.currentPage = 1
            self.loadPage(1)
            self.updateTable()
            self.update_page_display()

    def last_page(self):
        """Navigate to the last page"""
        total_pages = (self.totalSubjects + self.pageSize - 1) // self.pageSize
        if self.currentPage < total_pages:
            self.currentPage = total_pages
            self.loadPage(total_pages)
            self.updateTable()
            self.update_page_display()

    def go_to_page(self, e):
        """Navigate to the page number entered in the input field"""
        try:
            page_num = int(e.value)
            if page_num < 1:
                page_num = 1
            elif page_num > (self.totalSubjects + self.pageSize - 1) // self.pageSize:
                page_num = (self.totalSubjects + self.pageSize - 1) // self.pageSize
            
            if page_num != self.currentPage:
                self.currentPage = page_num
                self.loadPage(page_num)
                self.updateTable()
                self.update_page_display()
        except ValueError:
            pass

    def update_page_display(self):
        """Update the page info display labels"""
        if self.page_info_label and self.page_count_label and self.page_goto_input:
            total_pages = (self.totalSubjects + self.pageSize - 1) // self.pageSize
            self.page_info_label.text = f'Page {self.currentPage} of {total_pages}'
            self.page_goto_input.value = str(self.currentPage)
            self.page_count_label.text = f'({self.totalSubjects} total subjects, {self.pageSize} per page)'
            logger.debug(f"Updated page display: Page {self.currentPage} of {total_pages}")

    # ========================================================================================
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

