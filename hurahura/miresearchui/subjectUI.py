import os
from nicegui import ui, app
from hurahura import mi_subject
from hurahura.miresearchui import miui_helpers
import inspect

os.environ["QT_QPA_PLATFORM"] = "offscreen"

@ui.page('/subject_page/{subjid}')
def subject_page(subjid: str, dataRoot: str, classPath: str):
    page = SubjectPage(subjid, dataRoot, classPath)
    page.build_page()


class SubjectPage:
    def __init__(self, subjid: str, dataRoot: str, classPath: str):
        self.thisSubj = miui_helpers.subjID_dataRoot_classPathTo_SubjObj(subjid, dataRoot, classPath)
        self.SubjClass = self.thisSubj.__class__
        
    def build_page(self):
        self._create_header()
        self._create_tabs()
        
    def _create_header(self):
        with ui.row():
            ui.button(icon='home', on_click=lambda: ui.navigate.to('/'))
            ui.label(f"{self.thisSubj.subjID}: {self.thisSubj.getName()} scanned on {self.thisSubj.getStudyDate()}").classes('text-h5')

    def _create_tabs(self):
        with ui.tabs().classes('w-full') as tabs:
            actions = ui.tab('Actions')
            study_overview = ui.tab('Study Overview')
            series_overview = ui.tab('Series Overview')
            logview = ui.tab('Logs')
        with ui.tab_panels(tabs, value=logview).classes('w-full'):
            with ui.tab_panel(actions):
                self._create_actions_panel()
            with ui.tab_panel(study_overview):
                self._create_study_panel()
            with ui.tab_panel(series_overview):
                self._create_series_panel()
            with ui.tab_panel(logview):
                self._create_log_panel()

    # ========================================================================================
    # ACTIONS PANEL
    # ========================================================================================  
    def _create_actions_panel(self):
        ui.label("ACTIONS auto collected from methods decorated with @ui.method.")
        ui.label("Set parameters in the input fields (default values are pre-populated) and click on a method to run it for this subject.")
        decorated_methods = self.SubjClass.get_ui_methods()
        for iMethod in decorated_methods:
            display_name = iMethod['name']
            # Convert camel case to spaced text, but keep consecutive capitals together
            display_name = ''.join(' ' + c if c.isupper() and (i > 0 and not display_name[i-1].isupper()) else c 
                                  for i, c in enumerate(display_name)).strip()
            display_name = display_name.replace('_', ' ').capitalize()
            
            with ui.row().classes('w-full items-center border-2 border-gray-300 rounded-lg p-4 mb-4'):
                # Create a column for input fields that takes most of the space
                with ui.column().classes('flex-grow'):
                    params = list(inspect.signature(iMethod['method']).parameters.items())[1:]  # Skip 'self'
                    input_fields = []
                    
                    # Organize input fields in rows of 3
                    for i in range(0, len(params), 3):
                        with ui.row().classes('w-full gap-4'):
                            for param_name, param in params[i:i+3]:
                                with ui.column().classes('flex-grow'):
                                    default_value = param.default if param.default != inspect.Parameter.empty else ''
                                    input_field = ui.input(label=param_name, value=default_value)
                                    input_fields.append(input_field)
                
                # Button column aligned to the right
                with ui.column().classes('ml-4'):
                    def handle_click(method=iMethod['method'], inputs=input_fields):
                        try:
                            args = [inp.value for inp in inputs]
                            method(self.thisSubj, *args)
                            ui.notify(f'Method {iMethod["name"]} completed', type='positive')
                        except Exception as e:
                            ui.notify(f'Error: {iMethod["name"]}: {str(e)}', type='negative')
                    
                    ui.button(display_name, on_click=handle_click).classes('self-end')

    # ========================================================================================
    # STUDY PANEL
    # ========================================================================================  
    def _create_study_panel(self):
        columnsO = [
            {'name': 'key', 'label': 'Key', 'field': 'key', 'align': 'left', 'sortable': True},
            {'name': 'value', 'label': 'Value', 'field': 'value', 'align': 'center'},
        ]
        studyLabels = ["PatientName", "PatientID", "PatientBirthDate", "PatientAge", "MagneticFieldStrength", 
                       "PatientSex", "StudyDate", "StudyDescription"]
        rowsO = []
        metaDict = self.thisSubj.getMetaDict()
        for iKey in studyLabels:
            rowsO.append({"key": iKey, "value": str(metaDict.get(iKey, 'UNKNOWN'))})
        with ui.column().classes('w-full'):
            ui.label("STUDY INFORMATION")
            ui.table(columns=columnsO, rows=rowsO, row_key='key')

    # ========================================================================================
    # SERIES PANEL
    # ========================================================================================  
    def _create_series_panel(self):
        columnsSe = [
            {'name': 'sernum', 'label': 'Series Number', 'field': 'sernum', 'align': 'left', 'sortable': True},
            {'name': 'serdesc', 'label': 'Series Description', 'field': 'serdesc', 'align': 'left', 'sortable': True},
            {'name': 'ndcm', 'label': 'Number Images', 'field': 'ndcm', 'align': 'center'},
        ]
        rowsSe = []
        metaDict = self.thisSubj.getMetaDict()
        seriesList = metaDict.get('Series', []) # Not actually reading dicoms here - just grabbing metadata
        for iSeries in seriesList:
            rowsSe.append({
                "sernum": iSeries.get('SeriesNumber', 'UNKNOWN'), 
                "serdesc": iSeries.get('SeriesDescription', 'UNKNOWN'), 
                "ndcm": iSeries.get('nSlice', 'UNKNOWN'), 
                "_series": iSeries
            })
        
        def on_select_series(e):
            dcmFile = f"{self.thisSubj.dataRoot}{os.sep}{self.thisSubj.subjID}{os.sep}{e.args[1]['_series']['DicomFileName']}"
            if os.path.exists(dcmFile):
                dcmS = mi_subject.spydcm.dcmTK.DicomSeries.setFromFileList([dcmFile], HIDE_PROGRESSBAR=True)
                fig = dcmS.overviewImage(RETURN_FIG=True)
                fig_container.clear()
                with fig_container:
                    with ui.matplotlib(figsize=(8, 8)).figure as uifig:
                        ax = uifig.gca()
                        ax_ = fig.gca()
                        ax.imshow(ax_.images[0].get_array(), cmap='gray')
                        ax.axis('off')
        ##
        with ui.column().classes('w-full'):
            ui.label("SERIES INFORMATION (select series for image overview)")
            with ui.row().classes('w-full'):
                table = ui.table(columns=columnsSe, rows=rowsSe, row_key='sernum', on_select=on_select_series,
                                 pagination={'rowsPerPage': 99, 'sortBy': 'sernum', 'page': 1})
                table.add_slot('body-cell-sernum', r'<td><a :href="props.row.url">{{ props.row.sernum }}</a></td>')
                table.on('rowClick', on_select_series)
                fig_container = ui.element()


    def _create_log_panel(self):
        columnsL = [
            {'name': 'time', 'label': 'Time', 'field': 'time', 'align': 'left'},
            {'name': 'level', 'label': 'Level', 'field': 'level', 'sortable': True, 'align': 'center'},
            {'name': 'message', 'label': 'Message', 'field': 'message', 'align': 'left'},
        ]
        with open(self.thisSubj.logfileName, 'r') as fid:
            logLines = fid.readlines()
        rowsL = []
        for iLine in logLines:
            parts = iLine.split("|")
            if len(parts) > 3:
                rowsL.append({"time": parts[0], "level": parts[1], "message": parts[3]})
            elif len(parts) == 3: # this and else account for prevoius or incompatible log formats
                rowsL.append({"time": parts[0], "level": parts[1], "message": parts[2]})
            else:
                rowsL.append({"time": "-", "level": "-", "message": iLine})
        ui.table(columns=columnsL, rows=rowsL, row_key='time')
