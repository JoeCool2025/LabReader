import PySimpleGUI as sg
from txt_reader import tsv_reader
from db_viewer import db2df
from db_editor import parseedit
import os
from export import export

view_options = ['Flag', 'Detect', 'Trace', 'Duplicate', 'Exclude', 'Chem_Group']
layout = [
    [sg.Button(button_text='View Database'), sg.Button(button_text='Import Lab Data'), sg.Checkbox('Mass Upload', key='-MULTI-', tooltip='Upload a folder with multiple EDD directories')],
    [sg.Text('Select Optional Data Columns to View')],
    [sg.Listbox(values=view_options, select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE, expand_x=True, size=(20, 6), key='-OPTCOLUMNS-')],
    [sg.HorizontalSeparator(thickness=4)],
    [sg.Button(button_text='Exit')]
]

header = ['id', 'Location', 'Analyte', 'CASN', 'Sample Date', 'Sample Time', 'Conc', 'Conc Units', 'MDL']
headergw = ['Location', 'X Coordinate', 'Y Coordinate', 'Matrix', 'Address', 'AOC', 'Layer', 'Top Well Depth', 'Bottom Well Depth', 'Top Screen Depth', 'Bottom Screen Depth', 'Ground Elevation', 'Well Elevation', 'Source\\Tail', 'Saturated Thickness', 'ST Units', 'Porosity']
headersoil = ['Location', 'X Coordinate', 'Y Coordinate', 'Matrix', 'Address', 'AOC', 'Thickness', 'Thickness Units', 'Bulk Density', 'BD Units', '% Low K']
headerpore = ['Location', 'X Coordinate', 'Y Coordinate', 'Matrix', 'Address', 'AOC']
headerother = ['Location', 'X Coordinate', 'Y Coordinate', 'Matrix', 'Address', 'AOC']

rkeys = {'-GW-': 'Groundwater', '-SOIL-': 'Soil', '-PORE-': 'Porewater'}

db_default_save = os.path.dirname(os.path.abspath(__file__))
file_split = db_default_save.split('\\')
x = 0
for dir in file_split:
    if '__LabReader' in dir and x != len(file_split)-1:   
        file_split = file_split[:x+1]
        break
    x += 1
db_default_save = '\\'.join(file_split)
db_default_save += '\\Databases'
last_file_folder = None
prev_db = None

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
    df_gw, gwloc, df_soil, soilloc, df_pore, poreloc, df_other, otherloc = db2df(db_path, user_columns)
    table_values = {
                    '-GWDATA-': make_editable_values(df_gw),
                    '-GWLOC-': make_editable_values(gwloc),
                    '-SOILDATA-': make_editable_values(df_soil),
                    '-SOILLOC-': make_editable_values(soilloc),
                    '-POREDATA-': make_editable_values(df_pore),
                    '-PORELOC-': make_editable_values(poreloc),
                    '-OTHERDATA-': make_editable_values(df_other),
                    '-OTHERLOC-': make_editable_values(otherloc),
                }
    return table_values

def make_db_layout(table_values, editable):
    table_definitions = [
        ('-GWDATA-', 'Groundwater Data', header),
        ('-GWLOC-', 'Groundwater Locations', headergw),
        ('-SOILDATA-', 'Soil Data', header),
        ('-SOILLOC-', 'Soil Locations', headersoil),
        ('-POREDATA-', 'Porewater Data', header),
        ('-PORELOC-', 'Porewater Locations', headerpore),
        ('-OTHERDATA-', 'Other Data', header),
        ('-OTHERLOC-', 'Other Locations', headerother),
    ]
    tabs = [
        sg.Tab(
            tab_title,
            [[sg.Table(
                values=table_values[table_key],
                headings=headings,
                num_rows=20,
                auto_size_columns=False,
                col_widths=[14] * len(headings),
                expand_x=True,
                expand_y=True,
                vertical_scroll_only=False,
                k=table_key,
                enable_cell_editing=editable,
                enable_events=editable,
            )]],
        )
        for table_key, tab_title, headings in table_definitions
        if table_values[table_key]
    ]
    return [[sg.TabGroup([tabs])], [sg.Button('Edit', disabled=editable), sg.Button('Save', disabled=not editable), sg.Button('Cancel', disabled=not editable), sg.Button('Export', disabled=editable)]]

while True:
    event, values = window.read()

    if event == 'Exit' or event == sg.WIN_CLOSED:
        break

    if event == 'Import Lab Data':
        if values['-MULTI-']:
            lab_folder = sg.popup_get_folder(message='Select mass upload folder')
            db_path = sg.popup_get_file(
                message='Select Existing Database\n(or cancel to create a new database)',
                file_types=(('.db', '*.db'),),
                initial_folder=db_default_save,
                default_path=prev_db
            )
            prev_db = db_path
            failed = []
            for dir in os.listdir(lab_folder):
                lab_file = f'{lab_folder}\\{dir}\\hzresult.txt'
                sample_file = f'{lab_folder}\\{dir}\\hzsample.txt'
                try:
                    imported_db_path = tsv_reader(lab_file, db_path, sample_file)
                    if imported_db_path is not None:
                        db_path = imported_db_path
                except:
                    failed.append(f'{lab_folder}\\{dir}')
            prev_db = db_path
            if len(failed) > 0:
                failed_win = sg.Window('Locations with an Error', [[sg.Text('The following folders were unable to be uploaded:')], [sg.Listbox(failed, size=(20, 10))]])
                while True:
                    efail, vfail = failed_win.read()
                    if efail == sg.WIN_CLOSED:
                        break
            else:
                sg.popup_quick_message('Upload Success!')                

        else:
            lab_file = sg.popup_get_file(
                message='Select EDD hzresult File',
                file_types=((".txt", "*.txt"), (".csv", "*.csv"), ("ALL Files", "*.*")),
                initial_folder=last_file_folder
            )
            if not lab_file:
                continue
            if not lab_file[-12:] == 'hzresult.txt':
                sg.popup_quick_message('Please Select a hzresult.txt file')
                continue
            last_file_folder = lab_file[:-13]

            if lab_file.lower().endswith('.txt'):
                while True:
                    sample_file = sg.popup_get_file(
                        'Select associated EDD hzsample file',
                        file_types=(('.txt', '*.txt'),)
                    )
                    if sample_file == None or not sample_file[-12:] == 'hzsample.txt':
                        sg.popup_quick_message('Please Select a hzsample.txt File')
                        continue
                    else:
                        break  
                db_path = sg.popup_get_file(
                    message='Select Existing Database\n(or cancel to create a new database)',
                    file_types=(('.db', '*.db'),),
                    initial_folder=db_default_save,
                    default_path=prev_db
                )
                prev_db = db_path
            imported_db_path = tsv_reader(lab_file, db_path, sample_file)
            if imported_db_path is not None:
                db_path = imported_db_path
                prev_db = db_path

    if event == 'View Database':
        db_path = sg.popup_get_file(
            message='Select Existing Database',
            file_types=((".db", "*.db"),),
            initial_folder=db_default_save,
            default_path=prev_db
        )
        prev_db = db_path
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
                '-GWLOC-': ['Location_Name', 'X_Coordinate', 'Y_Coordinate', 'Matrix', 'Address', 'AOC', 'Layer', 'Depth_To_Top_Of_Well', 'Depth_To_Bottom_Of_Well', 'Depth_To_Top_Of_Screen', 'Depth_To_Bottom_Of_Screen', 'Ground_Elevation', 'Well_Elevation', 'Source_Tail', 'Saturated_Thickness', 'Units_of_ST', 'Porosity'],
                '-SOILDATA-': ['id', 'Location_Name', 'Analyte', 'CASN', 'Sample_Date', 'Result', 'Result_Unit', 'Method_Detection_Limit'] + user_columns,
                '-SOILLOC-': ['Location_Name', 'X_Coordinate', 'Y_Coordinate', 'Matrix', 'Address', 'AOC', 'Thickness', 'Units_of_Thickness', 'Bulk_Density', 'Units_of_Bulk_Density', 'Percent_Low_K'],
                '-POREDATA-': ['id', 'Location_Name', 'Analyte', 'CASN', 'Sample_Date', 'Result', 'Result_Unit', 'Method_Detection_Limit'] + user_columns,
                '-PORELOC-': ['Location_Name', 'X_Coordinate', 'Y_Coordinate', 'Matrix', 'Address', 'AOC'],
                '-OTHERDATA-': ['id', 'Location_Name', 'Analyte', 'CASN', 'Sample_Date', 'Result', 'Result_Unit', 'Method_Detection_Limit'] + user_columns,
                '-OTHERLOC-': ['Location_Name', 'X_Coordinate', 'Y_Coordinate', 'Matrix', 'Address', 'AOC'],
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
                    else:
                        parseedit(edits, db_path)
                        edit_toggle = False
                    dbwin.close()
                    table_values = get_table_values(db_path, user_columns)
                    dbwin = dbwindow(make_db_layout(table_values, edit_toggle))

                if e2 == 'Export':
                    export(db_path, user_columns)
