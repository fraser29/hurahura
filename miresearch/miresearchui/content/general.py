
import os
from nicegui import ui

from miresearch import mi_subject


@ui.page('/subject_page/{subjid}')
def subject_page(subjid: str, dataRoot: str=os.path.expanduser("~")):
    thisSubj = mi_subject.AbstractSubject(subjid, dataRoot=dataRoot)
    with ui.row():
        ui.button(icon='home', on_click=lambda: ui.navigate.to('/'))
        ui.label(f"{thisSubj.subjID}: {thisSubj.getName()} scanned on {thisSubj.getStudyDate()}").classes('text-h5')

    # def updateLog(log_box):
    #     log_box.push(f'new text {thisSubj.subjID} @ {thisSubj.getTopDir()}')


    with ui.tabs().classes('w-full') as tabs:
        overview = ui.tab('Overview')
        logview = ui.tab('Logs')
    with ui.tab_panels(tabs, value=logview).classes('w-full'):
        with ui.tab_panel(overview):
            columnsO = [
                {'name': 'key', 'label': 'Key', 'field': 'key', 'align': 'left', 'sortable': True},
                {'name': 'value', 'label': 'Value', 'field': 'value', 'align': 'center'},
            ]
            ui.label(f"STUDY INFORMATION")
            studyLabels = ["PatientName", "PatientID", "PatientBirthDate", "PatientAge", "MagneticFieldStrength", 
                           "PatientSex", "StudyDate", "StudyDescription"]
            rowsO = []
            metaDict = thisSubj.getMetaDict()
            for iKey in studyLabels:
                rowsO.append({"key": iKey, "value": str(metaDict[iKey])})
            ui.table(columns=columnsO, rows=rowsO, row_key='key')

            ui.label(f"SERIES INFORMATION") # TODO
            columnsSe = [
                {'name': 'serdesc', 'label': 'Series Description', 'field': 'serdesc', 'align': 'left', 'sortable': True},
                {'name': 'ndcm', 'label': 'Number Images', 'field': 'ndcm', 'align': 'center'},
            ]
            rowsSe = []
            seriesList = metaDict['Series']
            for iSeries in seriesList:
                rowsSe.append({"serdesc": iSeries.get('SeriesDescription', 'UNKNOWN'), 
                              "ndcm": len(iSeries)})
            ui.table(columns=columnsSe, rows=rowsSe, row_key='key')

        with ui.tab_panel(logview):
            columnsL = [
                {'name': 'time', 'label': 'Time', 'field': 'time', 'align': 'left'},
                {'name': 'level', 'label': 'Level', 'field': 'level', 'sortable': True, 'align': 'center'},
                {'name': 'message', 'label': 'Message', 'field': 'message', 'align': 'left'},
            ]
            with open(thisSubj.logfileName, 'r') as fid:
                logLines = fid.readlines()
            rowsL = []
            for iLine in logLines:
                parts = iLine.split("|")
                rowsL.append({"time": parts[0], "level": parts[1], "message": parts[3]})
            ui.table(columns=columnsL, rows=rowsL, row_key='time')
            # Maybe a refresh button for the logs? 

            # logBox = ui.log().classes('w-full h-20')
            # ui.button('Refresh', on_click=lambda: updateLog(logBox))
        
        # other tabs : 
        #   list images - another table
        #   3D view ? FDQ would be ok. 
        #   FDQ - can show results. / markup ? / execute action ? 
