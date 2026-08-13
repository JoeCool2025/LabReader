import PySimpleGUI as sg
from txt_reader import tsv_reader
from db_viewer import db2df

view_options = ['Flag', 'Detect', 'Trace', 'Duplicate', 'Exclude', 'Chem_Group']

layout = [
    [sg.Button(button_text='View Database'), sg.Button(button_text='Import Lab Data')],
    [sg.Text('Select Optional Data Columns to View')],
    [sg.Listbox(values=view_options, select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE, expand_x=True, size=(20, 6), key='-OPTCOLUMNS-')],
    [sg.HorizontalSeparator(thickness=4)],
    [sg.Button(button_text='Exit')]
]

header = ['Location', 'Analyte', 'CASN', 'Sample Date', 'Conc', 'Conc Units', 'MDL']
headergw = ['Location', 'X Coordinate', 'Y Coordinate', 'Longitude', 'Latitude', 'Layer', 'Source\\Tail', 'Saturated Thickness', 'ST Units', 'Porosity']
headersoil = ['Location', 'X Coordinate', 'Y Coordinate', 'Longitude', 'Latitude', 'Thickness', 'Thickness Units', 'Bulk Density', 'BD Units', '% Low K']
headerpore = ['Location', 'X Coordinate', 'Y Coordinate', 'Longitude', 'Latitude']

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
            user_columns = values['-OPTCOLUMNS-']
            header += user_columns
            try:
                df_gw, gwloc, df_soil, soilloc, df_pore, poreloc = db2df(db_path, user_columns)
            except Exception as e:
                print(e)
                break
            sg.Window('Database View', [[sg.TabGroup([[
                sg.Tab('Groundwater Data', [[sg.Table(values=df_gw, headings=header, expand_x=True, expand_y=True, vertical_scroll_only=False)]]),
                sg.Tab('Groundwater Locations', [[sg.Table(values=gwloc, headings=headergw, expand_x=True, expand_y=True, vertical_scroll_only=False)]]),
                sg.Tab('Soil Data', [[sg.Table(values=df_soil, headings=header, expand_x=True, expand_y=True, vertical_scroll_only=False)]]),
                sg.Tab('Soil Locations', [[sg.Table(values=soilloc, headings=headersoil, expand_x=True, expand_y=True, vertical_scroll_only=False)]]),
                sg.Tab('Porewater Data', [[sg.Table(values=df_pore, headings=header, expand_x=True, expand_y=True, vertical_scroll_only=False)]]),
                sg.Tab('Porewater Locations', [[sg.Table(values=poreloc, headings=headerpore, expand_x=True, expand_y=True, vertical_scroll_only=False)]])
            ]])]]).read()
