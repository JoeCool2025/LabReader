import PySimpleGUI as sg
from txt_reader import tsv_reader
from db_viewer import db2df

current_sites = []

layout = [
    [sg.Button(button_text='Import Lab Data'), sg.Button(button_text='View Database')],
    [sg.HorizontalSeparator(thickness=4)],
    [sg.Button(button_text='Exit')]
]

header = ['Location', 'Analyte', 'CASN', 'Sample Date', 'Conc', 'Conc Units', 'MDL']
checkgw = False
checksoil = False
checkpore = False

rkeys = {'-GW-': 'Groundwater', '-SOIL-': 'Soil', '-PORE-': 'Porewater'}
selection_layout = [
    [sg.Radio('Groundwater', group_id='group1', key='-GW-', enable_events=True),
     sg.Radio('Soil', group_id='group1', key='-SOIL-', enable_events=True),
     sg.Radio('Porewater', group_id='group1', key='-PORE-', enable_events=True)],
    [sg.Button(button_text='Select', key='-SELECT-', disabled=True)]
]

window = sg.Window('Window Title', layout)

while True:
    event, values = window.read()

    if event == 'Exit' or event == sg.WIN_CLOSED:
        break

    if event == 'Import Lab Data':
        lab_file = sg.popup_get_file(
            message='Select Lab File',
            file_types=((".txt", "*.txt"), (".csv", "*.csv"), ("ALL Files", "*.*"))
        )
        if not lab_file:
            continue

        selection = sg.Window('Lab Selection', selection_layout, modal=True)
        labtype = None

        while True:
            e1, v1 = selection.read()
            if e1 in (sg.WIN_CLOSED, 'Cancel'):
                labtype = None
                break

            if e1 in rkeys:
                selection['-SELECT-'].update(disabled=False)

            if e1 == '-SELECT-':
                selected_keys = [key for key in rkeys if v1.get(key)]
                if selected_keys:
                    labtype = rkeys[selected_keys[0]]
                    break

        selection.close()

        if labtype is None:
            continue

        if lab_file.lower().endswith('.txt'):
            db_path = sg.popup_get_file(
                message='Select Existing Database\n(or cancel to create a new database)',
                file_types=(('.db', '*.db'),)
            )
            tsv_reader(lab_file, db_path, labtype)

    if event == 'View Database':
        db_path = sg.popup_get_file(message='Select Existing Database', file_types=((".db", "*.db"),))
        if db_path != None and db_path != '':
            user_columns = []
            try:
                df_gw, df_soil, df_pore = db2df(db_path)
            except Exception as e:
                print(e)
                break
            sg.Window('Database View', [[sg.TabGroup([[
                sg.Tab('Groundwater Data', [[sg.Table(values=df_gw, headings=header, expand_x=True, expand_y=True, vertical_scroll_only=False, enable_cell_editing=True)]], disabled=checkgw),
                sg.Tab('Soil Data', [[sg.Table(values=df_soil, headings=header, expand_x=True, expand_y=True, vertical_scroll_only=False)]], disabled=checksoil),
                sg.Tab('Porewater Data', [[sg.Table(values=df_pore, headings=header, expand_x=True, expand_y=True, vertical_scroll_only=False)]], disabled=checkpore)
            ]])]]).read()
