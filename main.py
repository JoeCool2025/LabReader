import PySimpleGUI as sg
from txt_reader import tsv_reader
from db_viewer import db2df
from db_editor import parseedit

view_options = ['Flag', 'Detect', 'Trace', 'Duplicate', 'Exclude', 'Chem_Group']
layout = [
    [sg.Button(button_text='View Database'), sg.Button(button_text='Import Lab Data')],
    [sg.Text('Select Optional Data Columns to View')],
    [sg.Listbox(values=view_options, select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE, expand_x=True, size=(20, 6), key='-OPTCOLUMNS-')],
    [sg.HorizontalSeparator(thickness=4)],
    [sg.Button(button_text='Exit')]
]

header = ['id', 'Location', 'Analyte', 'CASN', 'Sample Date', 'Sample Time', 'Conc', 'Conc Units', 'MDL']
headergw = ['Location', 'X Coordinate', 'Y Coordinate', 'Longitude', 'Latitude', 'Matrix', 'Address', 'AOC', 'Layer', 'Top Well Depth', 'Bottom Well Depth', 'Top Screen Depth', 'Bottom Screen Depth', 'Ground Elevation', 'Well Elevation', 'Source\\Tail', 'Saturated Thickness', 'ST Units', 'Porosity']
headersoil = ['Location', 'X Coordinate', 'Y Coordinate', 'Longitude', 'Latitude', 'Matrix', 'Address', 'AOC', 'Thickness', 'Thickness Units', 'Bulk Density', 'BD Units', '% Low K']
headerpore = ['Location', 'X Coordinate', 'Y Coordinate', 'Longitude', 'Latitude', 'Matrix', 'Address', 'AOC']

rkeys = {'-GW-': 'Groundwater', '-SOIL-': 'Soil', '-PORE-': 'Porewater'}

def make_selection_layout():
    return [
        [
            sg.Radio('Groundwater', group_id='group1', key='-GW-', enable_events=True),
            sg.Radio('Soil', group_id='group1', key='-SOIL-', enable_events=True),
            sg.Radio('Porewater', group_id='group1', key='-PORE-', enable_events=True),
        ],
        [sg.Button(button_text='Select', key='-SELECT-', disabled=True)],
    ]

window = sg.Window('ESI Database Viewer', layout)
def dbwindow(dblayout):
    screen_width, screen_height = sg.Window.get_screen_size()
    dbwin = sg.Window(
        'Database',
        dblayout,
        size=(int(screen_width * 0.9), int(screen_height * 0.8)),
        resizable=True,
    )
    return dbwin

def values_equal(first, second):
    if first != first and second != second:
        return True
    return first == second

def make_editable_values(rows):
    return [
        ['' if value is None or value != value else value for value in row]
        for row in rows
    ]

def get_table_values(db_path, user_columns):
    df_gw, gwloc, df_soil, soilloc, df_pore, poreloc = db2df(db_path, user_columns)
    table_values = {
                    '-GWDATA-': make_editable_values(df_gw),
                    '-GWLOC-': make_editable_values(gwloc),
                    '-SOILDATA-': make_editable_values(df_soil),
                    '-SOILLOC-': make_editable_values(soilloc),
                    '-POREDATA-': make_editable_values(df_pore),
                    '-PORELOC-': make_editable_values(poreloc),
                }
    return table_values

def make_db_layout(table_values, editable):
    return [[sg.TabGroup([[
        sg.Tab('Groundwater Data', [[sg.Table(values=table_values['-GWDATA-'], headings=header, num_rows=20, auto_size_columns=False, col_widths=[14] * len(header), expand_x=True, expand_y=True, vertical_scroll_only=False, k='-GWDATA-', enable_cell_editing=editable, enable_events=editable)]]),
        sg.Tab('Groundwater Locations', [[sg.Table(values=table_values['-GWLOC-'], headings=headergw, num_rows=20, auto_size_columns=False, col_widths=[14] * len(headergw), expand_x=True, expand_y=True, vertical_scroll_only=False, k='-GWLOC-', enable_cell_editing=editable, enable_events=editable)]]),
        sg.Tab('Soil Data', [[sg.Table(values=table_values['-SOILDATA-'], headings=header, num_rows=20, auto_size_columns=False, col_widths=[14] * len(header), expand_x=True, expand_y=True, vertical_scroll_only=False, k='-SOILDATA-', enable_cell_editing=editable, enable_events=editable)]]),
        sg.Tab('Soil Locations', [[sg.Table(values=table_values['-SOILLOC-'], headings=headersoil, num_rows=20, auto_size_columns=False, col_widths=[14] * len(headersoil), expand_x=True, expand_y=True, vertical_scroll_only=False, k='-SOILLOC-', enable_cell_editing=editable, enable_events=editable)]]),
        sg.Tab('Porewater Data', [[sg.Table(values=table_values['-POREDATA-'], headings=header, num_rows=20, auto_size_columns=False, col_widths=[14] * len(header), expand_x=True, expand_y=True, vertical_scroll_only=False, k='-POREDATA-', enable_cell_editing=editable, enable_events=editable)]]),
        sg.Tab('Porewater Locations', [[sg.Table(values=table_values['-PORELOC-'], headings=headerpore, num_rows=20, auto_size_columns=False, col_widths=[14] * len(headerpore), expand_x=True, expand_y=True, vertical_scroll_only=False, k='-PORELOC-', enable_cell_editing=editable, enable_events=editable)]])
    ]])], [sg.Button('Edit', disabled=editable), sg.Button('Save', disabled=not editable), sg.Button('Cancel', disabled=not editable)]]

while True:
    event, values = window.read()

    if event == 'Exit' or event == sg.WIN_CLOSED:
        break

    if event == 'Import Lab Data':
        lab_file = sg.popup_get_file(
            message='Select EDD hzresult File',
            file_types=((".txt", "*.txt"), (".csv", "*.csv"), ("ALL Files", "*.*"))
        )
        if not lab_file:
            continue
        if not lab_file[-12:] == 'hzresult.txt':
            sg.popup_quick_message('Please Select a hzresult.txt file')
            continue

        selection = sg.Window('Lab Selection', make_selection_layout(), modal=True)
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
            while True:
                sample_file = sg.popup_get_file('Select associated EDD hzsample file', file_types=(('.txt', '*.txt'),))
                if sample_file[-12:] == 'hzsample.txt':
                    break
                else:
                    sg.popup_quick_message('Please Select a hzsample.txt File')   
            db_path = sg.popup_get_file(
                message='Select Existing Database\n(or cancel to create a new database)',
                file_types=(('.db', '*.db'),)
            )
            tsv_reader(lab_file, db_path, labtype, sample_file)

    if event == 'View Database':
        db_path = sg.popup_get_file(message='Select Existing Database', file_types=((".db", "*.db"),))
        if db_path != None and db_path != '':
            user_columns = values['-OPTCOLUMNS-']
            header += user_columns
            try:
                table_values = get_table_values(db_path, user_columns)
            except Exception as e:
                print(e)
                break
            table_columns = {
                '-GWDATA-': ['id', 'Location_Name', 'Analyte', 'CASN', 'Sample_Date', 'Result', 'Result_Unit', 'Method_Detection_Limit'] + user_columns,
                '-GWLOC-': ['Location_Name', 'X_Coordinate', 'Y_Coordinate', 'Longitude', 'Latitude', 'Matrix', 'Address', 'AOC', 'Layer', 'Depth_To_Top_Of_Well', 'Depth_To_Bottom_Of_Well', 'Depth_To_Top_Of_Screen', 'Depth_To_Bottom_Of_Screen', 'Ground_Elevation', 'Well_Elevation', 'Source_Tail', 'Saturated_Thickness', 'Units_of_ST', 'Porosity'],
                '-SOILDATA-': ['id', 'Location_Name', 'Analyte', 'CASN', 'Sample_Date', 'Result', 'Result_Unit', 'Method_Detection_Limit'] + user_columns,
                '-SOILLOC-': ['Location_Name', 'X_Coordinate', 'Y_Coordinate', 'Longitude', 'Latitude', 'Matrix', 'Address', 'AOC', 'Thickness', 'Units_of_Thickness', 'Bulk_Density', 'Units_of_Bulk_Density', 'Percent_Low_K'],
                '-POREDATA-': ['id', 'Location_Name', 'Analyte', 'CASN', 'Sample_Date', 'Result', 'Result_Unit', 'Method_Detection_Limit'] + user_columns,
                '-PORELOC-': ['Location_Name', 'X_Coordinate', 'Y_Coordinate', 'Longitude', 'Latitude', 'Matrix', 'Address', 'AOC'],
            }
            original_table_values = {
                table_key: [row.copy() for row in rows]
                for table_key, rows in table_values.items()
            }
            edit_toggle = False
            dbwin = dbwindow(make_db_layout(table_values, edit_toggle))
            edits = []
            while True:
                e2, v2 = dbwin.read()

                if e2 == sg.WIN_CLOSED:
                    break

                edited_table = None
                edited_cell = None
                if isinstance(e2, tuple) and len(e2) == 3 and e2[0] in table_values:
                    edited_table = e2[0]
                    edited_cell = e2[2]

                if e2 == 'Edit':
                    edit_toggle = True
                    dbwin.close()
                    dbwin = dbwindow(make_db_layout(get_table_values(db_path, user_columns), edit_toggle))

                if e2 == 'Cancel':
                    edit_toggle = False
                    edits.clear()
                    dbwin.close()
                    dbwin = dbwindow(make_db_layout(get_table_values(db_path, user_columns), edit_toggle))

                if edited_table is not None and edited_cell is not None:
                    table = dbwin[edited_table]
                    current_values = table.Values
                    row_idx, col_idx = edited_cell
                    if row_idx < len(current_values) and col_idx < len(current_values[row_idx]):
                        new_val = current_values[row_idx][col_idx]
                        row_key = current_values[row_idx][0]
                        col_key = table_columns[edited_table][col_idx]
                        edits.append({"table": edited_table, "row": row_key, "col": col_key, "value": new_val})
                        table_values[edited_table] = [row.copy() for row in current_values]

                if e2 == 'Save':
                    if not edits:
                        sg.popup('No edits to save')
                        continue
                    parseedit(edits, db_path)
                    dbwin.close()
                    table_values = get_table_values(db_path, user_columns)
                    dbwin = dbwindow(make_db_layout(table_values, edit_toggle))
