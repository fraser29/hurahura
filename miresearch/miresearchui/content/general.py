import os
from nicegui import ui
from miresearch import mi_subject


@ui.page('/subject_page/{subjid}')
def subject_page(subjid: str, dataRoot: str = os.path.expanduser("~")):
    page = SubjectPage(subjid, dataRoot)
    page.build_page()


class SubjectPage:
    def __init__(self, subjid: str, dataRoot: str = os.path.expanduser("~")):
        self.subjid = subjid
        self.dataRoot = dataRoot
        self.thisSubj = mi_subject.AbstractSubject(subjid, dataRoot=dataRoot)
        
    def build_page(self):
        self._create_header()
        self._create_tabs()
        
    def _create_header(self):
        with ui.row():
            ui.button(icon='home', on_click=lambda: ui.navigate.to('/'))
            ui.label(f"{self.thisSubj.subjID}: {self.thisSubj.getName()} scanned on {self.thisSubj.getStudyDate()}").classes('text-h5')

    def _create_tabs(self):
        with ui.tabs().classes('w-full') as tabs:
            overview = ui.tab('Overview')
            logview = ui.tab('Logs')
        with ui.tab_panels(tabs, value=logview).classes('w-full'):
            with ui.tab_panel(overview):
                self._create_overview_panel()
            with ui.tab_panel(logview):
                self._create_log_panel()

    def _create_overview_panel(self):
        self._create_study_info()
        self._create_series_info()

    def _create_study_info(self):
        columnsO = [
            {'name': 'key', 'label': 'Key', 'field': 'key', 'align': 'left', 'sortable': True},
            {'name': 'value', 'label': 'Value', 'field': 'value', 'align': 'center'},
        ]
        ui.label("STUDY INFORMATION")
        studyLabels = ["PatientName", "PatientID", "PatientBirthDate", "PatientAge", "MagneticFieldStrength", 
                       "PatientSex", "StudyDate", "StudyDescription"]
        rowsO = []
        metaDict = self.thisSubj.getMetaDict()
        for iKey in studyLabels:
            rowsO.append({"key": iKey, "value": str(metaDict[iKey])})
        ui.table(columns=columnsO, rows=rowsO, row_key='key')

    def _create_series_info(self):
        ui.label("SERIES INFORMATION")
        columnsSe = [
            {'name': 'sernum', 'label': 'Series Number', 'field': 'sernum', 'align': 'left', 'sortable': True},
            {'name': 'serdesc', 'label': 'Series Description', 'field': 'serdesc', 'align': 'left', 'sortable': True},
            {'name': 'ndcm', 'label': 'Number Images', 'field': 'ndcm', 'align': 'center'},
        ]
        rowsSe = []
        metaDict = self.thisSubj.getMetaDict()
        seriesList = metaDict['Series'] # Not actually reading dicoms here - just grabbing metadata
        for iSeries in seriesList:
            rowsSe.append({
                "sernum": iSeries.get('SeriesNumber', 'UNKNOWN'), 
                "serdesc": iSeries.get('SeriesDescription', 'UNKNOWN'), 
                "ndcm": len(iSeries),
                "_series": iSeries
            })
        
        fig_container = ui.element()
        
        def on_select(e):
            dcmFile = f"{self.thisSubj.dataRoot}{os.sep}{self.thisSubj.subjID}{os.sep}{e.args[1]['_series']['DicomFileName']}"
            if os.path.exists(dcmFile):
                dcmS = mi_subject.spydcm.dcmTK.DicomSeries.setFromFileList([dcmFile], HIDE_PROGRESSBAR=True)
                fig = dcmS.buildOverviewImage(RETURN_FIG=True)
                fig_container.clear()
                with fig_container:
                    with ui.matplotlib(figsize=(3, 2)).figure as uifig:
                        ax = uifig.gca()
                        ax_ = fig.gca()
                        ax.imshow(ax_.images[0].get_array())
                        ax.axis('off')
        
        table = ui.table(columns=columnsSe, rows=rowsSe, row_key='sernum', on_select=on_select)
        table.add_slot('body-cell-sernum', r'<td><a :href="props.row.url">{{ props.row.sernum }}</a></td>')
        table.on('rowClick', on_select)
        
        with ui.column():
            fig_container

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
            rowsL.append({"time": parts[0], "level": parts[1], "message": parts[3]})
        ui.table(columns=columnsL, rows=rowsL, row_key='time')
