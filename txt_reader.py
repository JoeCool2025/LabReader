import pandas as pd
import PySimpleGUI as sg
from contextlib import contextmanager
from casn_lookup import casn_search
from sqlalchemy import (
    Insert,
    MetaData,
    Table,
    select,
    create_engine,
    exc,
    Update,
    text
)
from make_db import db_maker
from type_selection import matrixselection

def clean_value(value):
    if pd.isna(value) or value == '':
        return None
    if hasattr(value, 'item'):
        value = value.item()
    return value

def address_layout(old, new):
    return [
        [
            sg.Radio(f'{old}', group_id='group2', key='-OLD-', enable_events=True),
            sg.Radio(f'{new}', group_id='group2', key='-NEW-', enable_events=True)
        ],
        [sg.Button('Select', key='-SELECT-', disabled=True)]
    ]

def standardize_address(conn, location_table, site, fieldid, address_cache):
    metadata_obj = MetaData()
    gw_location_table = Table('gw_locations', metadata_obj, autoload_with=conn)
    soil_location_table = Table('soil_locations', metadata_obj, autoload_with=conn)
    porewater_location_table = Table('porewater_locations', metadata_obj, autoload_with=conn)
    other_location_table = Table('other_locations', metadata_obj, autoload_with=conn)
    table_list = [gw_location_table, soil_location_table, porewater_location_table, other_location_table]
    options = []

    for table in table_list:
        result = conn.execute(text(f'SELECT DISTINCT Address from {table.name}'))
        for row in result:
            if row.Address not in options:
                options.append(row.Address)

    if fieldid in options or options == []:
        return fieldid
    if fieldid in address_cache:
        return address_cache[fieldid]
    address_correction = sg.Window(
        'Address Standardization',
        address_layout(options[0], fieldid),
        modal=True,
    )
    try:
        while True:
            event, values = address_correction.read()
            if event in (sg.WINDOW_CLOSED, sg.WIN_CLOSED):
                return options[0]
            if event in ('-OLD-', '-NEW-'):
                address_correction['-SELECT-'].update(disabled=False)
            if event == '-SELECT-':
                if values.get('-NEW-'):
                    for table in table_list:
                        conn.execute(
                            Update(table),
                            [{'Address': fieldid}],
                        )
                    address_cache[fieldid] = fieldid
                    return fieldid
                address_cache[fieldid] = options[0]
                return options[0]
    finally:
        address_correction.close()

@contextmanager
def import_transaction(engine, progress_window):
    try:
        with engine.begin() as conn:
            yield conn
    finally:
        progress_window.close()

MATRIX_LABELS = {
    'groundwater': 'Groundwater',
    'ground water': 'Groundwater',
    'soil': 'Soil',
    'porewater': 'Porewater',
    'pore water': 'Porewater',
}

def assign_matrix_values(df, selection_type, selection):
    # Assign/reassign matrix values to recognizable strings
    df['Matrix'] = df['Matrix'].astype(object)
    if selection_type == 1: # if all in document are the same
        df['Matrix'] = selection
    elif selection_type == 2: # site by site
        for location, matrix in selection.items():
            df.loc[df['Sampnum'] == location, 'Matrix'] = matrix
    return df

def make_site_name(location, sample_date):
    # Add uniqueness for trip blanks, field blanks, duplicates
    if isinstance(location, str) and len(location) >= 5 and location[-5] == '-' and location[-4:].isdigit():
        if location[:2].lower() in ('tb', 'fb') or location[:3].lower() == 'dup':
            return location[:-5] + '-' + sample_date.strftime('%m%Y')
        return location[:-5]
    if isinstance(location, str) and (location[:2].lower() in ('tb', 'fb') or location[:3].lower() == 'dup'):
        return location + '-' + sample_date.strftime('%m%Y')
    return location

def make_result_record(location, analyte, casn, sample_date, result, result_unit, mdl, flag):
    # Build the shared result fields used by each matrix-specific table
    try:
        if result.lower() == 'nd':
            result = None
    except AttributeError:
        pass
    return {
        'Location_Name': location,
        'Analyte': analyte,
        'CASN': casn,
        'Sample_Date': sample_date,
        'Result': result,
        'Result_Unit': result_unit,
        'Method_Detection_Limit': mdl,
        'Flag': flag,
        'Detect': flag != 'U',
        'Trace': flag in ('J', 'TR'),
        'Duplicate': location[:3] == 'DUP',
        'Exclude': False,
    }

def insert_result(conn, data_table, result_record, mark_non_total_as_total=False):
    # Insert a result and mark TOTAL analytes as belonging to Chem_Group TOT
    conn.execute(Insert(data_table), [result_record])
    if mark_non_total_as_total or result_record['Analyte'][-5:] == 'TOTAL':
        conn.execute(
            Update(data_table).where(data_table.c.Analyte == result_record['Analyte']),
            [{'Chem_Group': 'TOT'}],
        )

def findlabtype(df):
    dict = {}
    loclist = []
    locmat = {}
    try:
        qaqc = df.at[0, 'Qaqc']
    except:
        try:
            qaqc = df.at[0, 'QAQC']
        except:
            qaqc = df.at[0, 'qaqc']
    for location in df.loc[:, 'Sampnum'].unique():
        loclist.append(location)
    for x in range(0, len(df)):
        l, m = df.loc[x, ['Sampnum', 'Matrix']]
        locmat[l] = m
    matrix_values = df.loc[:, 'Matrix'].unique()
    invalid_matrix_found = any(
        not isinstance(matrix, str) or matrix.strip().lower() not in MATRIX_LABELS
        for matrix in matrix_values
    )
    if not invalid_matrix_found:
        normalized_matrices = {
            location: MATRIX_LABELS[matrix.strip().lower()]
            for location, matrix in zip(df['Sampnum'], df['Matrix'])
        }
        unique_matrices = set(normalized_matrices.values())
        if len(unique_matrices) == 1:
            return 1, unique_matrices.pop()
        return 2, normalized_matrices

    layout4 = [
        [sg.Text('Please input Matrices')]
    ]
    matrix = matrixselection(qaqc)
    if matrix == 'Mixed':
        if len(loclist) <= 0:
            return 2, dict
        
        for loc in loclist:
            layout4.append([sg.Text(f'Matrix for {loc}: '), sg.Input(default_text=f'{locmat[loc]}', key=f'-{loc}-')])
        layout4.append([sg.Button('Confirm Selection')])
        otherwin = sg.Window('Other sites', layout4, enable_close_attempted_event=True)
        while True:
            otherevent, othervalues = otherwin.read()

            if otherevent == 'Confirm Selection':
                for loc in loclist:
                    dict[loc] = othervalues[f'-{loc}-']
                otherwin.close()
                break
            if otherevent == sg.WIN_CLOSE_ATTEMPTED_EVENT:
                sg.popup_quick_message('Please Input Other Matrices')
                continue
        return 2, dict
    elif matrix not in ('Groundwater', 'Soil', 'Porewater'):
        return 3, matrix
    return 1, matrix

def _validate_import_data(file, samp_file):
    """Parse the input files and exercise conversions used by the importer."""
    df = pd.read_csv(file, sep='\t')
    df2 = pd.read_csv(samp_file, sep='\t')
    v, m = findlabtype(df2)
    df2 = assign_matrix_values(df2, v, m)
    mapping = df2.set_index('Sampnum')['Matrix']
    df['Matrix'] = df['Sampnum'].map(mapping)

    required_result_columns = {
        'QAQC', 'Sampnum', 'Sampdate', 'Analtparam', 'Cas',
        'Conc', 'Concunits', 'Mdl', 'Qaqual',
    }
    missing_result_columns = required_result_columns - set(df.columns)
    if missing_result_columns:
        raise ValueError(
            f"Missing hzresult columns: {', '.join(sorted(missing_result_columns))}"
        )

    required_sample_columns = {'Sampnum', 'Matrix', 'Samptime'}
    missing_sample_columns = required_sample_columns - set(df2.columns)
    if missing_sample_columns:
        raise ValueError(
            f"Missing hzsample columns: {', '.join(sorted(missing_sample_columns))}"
        )

    for value in df['Sampdate']:
        pd.to_datetime(value)
    for value in df2['Samptime'].map(clean_value):
        if value is not None:
            pd.to_datetime(value).time()

    return df, df2


def tsv_reader(file, db, samp_file):
    try:
        df, df2 = _validate_import_data(file, samp_file)
        return _import_tsv(file, db, samp_file, df, df2)
    except Exception as error:
        sg.popup_error(f'Unable to import lab data:\n{error}')
        return None


def _import_tsv(file, db, samp_file, df, df2):
    if db == None or db == '':
        db_path = db_maker(file)
    else:
        db_path = db
    mapping = df2.set_index('Sampnum')['Matrix']

    engine = create_engine(f'sqlite:///{db_path}')
    metadata_obj = MetaData()
    metadata_obj.create_all(engine)
    gw_location_table = Table('gw_locations', metadata_obj, autoload_with=engine)
    gw_data = Table('gw_results', metadata_obj, autoload_with=engine)
    soil_location_table = Table('soil_locations', metadata_obj, autoload_with=engine)
    soil_data = Table('soil_results', metadata_obj, autoload_with=engine)
    porewater_location_table = Table('porewater_locations', metadata_obj, autoload_with=engine)
    porewater_data = Table('porewater_results', metadata_obj, autoload_with=engine)
    other_location_table = Table('other_locations', metadata_obj, autoload_with=engine)
    other_data = Table('other_results', metadata_obj, autoload_with=engine)

    location_tables = {
        'Groundwater': gw_location_table,
        'Soil': soil_location_table,
        'Porewater': porewater_location_table,
    }
    address_table = {
        'Groundwater': 'gw',
        'Soil': 'soil',
        'Porewater': 'porewater'
    }

    location_count = len(df.loc[:, 'Sampnum'].unique())
    
    progress_total = location_count + len(df)
    progress_value = 0
    progress_window = sg.Window(
        'Importing Lab Data',
        [
            [sg.Text('Importing lab data...')],
            [sg.ProgressBar(progress_total, orientation='h', size=(40, 20), key='-IMPORT-PROGRESS-')],
        ],
        finalize=True,
    )

    def update_progress():
        nonlocal progress_value
        progress_value += 1
        progress_window['-IMPORT-PROGRESS-'].update(progress_value)
        progress_window.read(timeout=0)

    address_cache = {}
    with import_transaction(engine, progress_window) as conn:
        # Keep the source data table in the same transaction as the import.
        try:
            df.to_sql(name=f"{df.at[0, 'QAQC']}", con=conn)
        except ValueError:
            sg.popup_quick_message('Lab Data already in Selected Database')
            return

        # First create one location row for every unique sample location.
        for row in df.loc[:, 'Sampnum'].unique():
            labtype = mapping.get(row)
            try:
                sampdate = pd.to_datetime(df.loc[df['Sampnum'] == row, 'Sampdate'].iloc[0])
            except IndexError:
                sampdate = pd.to_datetime(sg.popup_get_date(title=f'No Date Found. Please provide date for {row}:'))
            site = make_site_name(row, sampdate)
            try:
                conn.execute(
                    Insert(location_tables[labtype]),
                    [{"Location_Name": site}],
                )
            except exc.IntegrityError:
                continue
            except KeyError:
                try:
                    conn.execute(
                        Insert(other_location_table),
                        [{'Location_Name': site}]
                    )
                except exc.IntegrityError:
                    continue

            xcoord = None
            ycoord = None

            if labtype == 'Groundwater':
                layer = None
                s_tail = None
                sat_thick = None
                stunit = None
                porosity = None
                conn.execute(
                    Update(gw_location_table)
                    .where(gw_location_table.c.Location_Name == site),
                    {
                        'X_Coordinate': xcoord,
                        'Y_Coordinate': ycoord,
                        'Layer': layer,
                        'Source_Tail': s_tail,
                        'Saturated_Thickness': sat_thick,
                        'Units_of_ST': stunit,
                        'Porosity': porosity,
                    }
                )
            elif labtype == 'Soil':
                thick = None
                thickunit = None
                bulkd = None
                bulkdunit = None
                perlowk = None
                conn.execute(
                    Update(soil_location_table)
                    .where(soil_location_table.c.Location_Name == site),
                    [{
                        'X_Coordinate': xcoord,
                        'Y_Coordinate': ycoord,
                        'Thickness': thick,
                        'Units_of_Thickness': thickunit,
                        'Bulk_Density': bulkd,
                        'Units_of_Bulk_Density': bulkdunit,
                        'Percent_Low_K': perlowk,
                    }]
                )
            elif labtype == 'Porewater':
                conn.execute(
                    Update(porewater_location_table)
                    .where(porewater_location_table.c.Location_Name == site),
                    [{
                        'X_Coordinate': xcoord,
                        'Y_Coordinate': ycoord,
                    }]
                )
            else:
                conn.execute(
                    Update(other_location_table)
                    .where(other_location_table.c.Location_Name == site),
                    [{
                        'X_Coordinate': xcoord,
                        'Y_Coordinate': ycoord,
                    }]
                )
            update_progress()

        # Then insert each result into the table selected by its matrix.
        for x in range(0, len(df)):
            result_sampnum = df.loc[x, 'Sampnum']
            labtype = clean_value(df.loc[x, 'Matrix'])
            location, analyte_name, casn, date, result, res_unit, mdl, flag = df.loc[x, ['Sampnum', 'Analtparam', 'Cas', 'Sampdate', 'Conc', 'Concunits', 'Mdl', 'Qaqual']]
            date = pd.to_datetime(date)
            site = make_site_name(location, date)
            result_record = make_result_record(
                site, analyte_name, casn, date, result, res_unit, mdl, flag
            )
            if labtype == 'Groundwater':
                insert_result(conn, gw_data, result_record)
                for x in df2.index[df2['Sampnum'] == result_sampnum]:
                    location, time, matrix, fieldid, aocid, spx, spy, depthtop, depthbot, groundel, wellel, screentop, screenbot = df2.loc[x, ['Sampnum', 'Samptime', 'Matrix', 'Fieldid', 'Aocid', 'Sp_x', 'Sp_y', 'Depth_top', 'Depth_botm', 'GroundElev', 'Well_elev', 'Screentop', 'Screenbot']]
                    location, time, matrix, fieldid, aocid, spx, spy, depthtop, depthbot, groundel, wellel, screentop, screenbot = [clean_value(value) for value in (location, time, matrix, fieldid, aocid, spx, spy, depthtop, depthbot, groundel, wellel, screentop, screenbot)]
                    location = site
                    time = pd.to_datetime(time).time()
                    fieldid = standardize_address(conn, gw_location_table, location, fieldid, address_cache)
                    conn.execute(
                        Update(gw_data).where(gw_data.c.Location_Name == location),
                        [{'Sample_Time': time}],
                    )
                    conn.execute(
                        Update(gw_location_table).where(gw_location_table.c.Location_Name == location),
                        [{
                            'Matrix': matrix,
                            'Address': fieldid,
                            'AOC': aocid,
                            'X_Coordinate': spx,
                            'Y_Coordinate': spy,
                            'Depth_To_Top_Of_Well': depthtop,
                            'Depth_To_Bottom_Of_Well': depthbot,
                            'Ground_Elevation': groundel,
                            'Well_Elevation': wellel,
                            'Depth_To_Top_Of_Screen': screentop,
                            'Depth_To_Bottom_Of_Screen': screenbot
                        }],
                    )
            elif labtype == 'Soil':
                insert_result(conn, soil_data, result_record, mark_non_total_as_total=True)
                for x in df2.index[df2['Sampnum'] == result_sampnum]:
                    location, time, matrix, fieldid, aocid, spx, spy = df2.loc[x, ['Sampnum', 'Samptime', 'Matrix', 'Fieldid', 'Aocid', 'Sp_x', 'Sp_y']]
                    location, time, matrix, fieldid, aocid, spx, spy = [clean_value(value) for value in (location, time, matrix, fieldid, aocid, spx, spy)]
                    location = site
                    time = pd.to_datetime(time).time()
                    fieldid = standardize_address(conn, soil_location_table, location, fieldid, address_cache)
                    conn.execute(
                        Update(soil_data).where(soil_data.c.Location_Name == location),
                        [{'Sample_Time': time}],
                    )
                    conn.execute(
                        Update(soil_location_table).where(soil_location_table.c.Location_Name == location),
                        [{
                            'Matrix': matrix,
                            'Address': fieldid,
                            'AOC': aocid,
                            'X_Coordinate': spx,
                            'Y_Coordinate': spy
                        }],
                    )
            elif labtype == 'Porewater':
                insert_result(conn, porewater_data, result_record)
                for x in df2.index[df2['Sampnum'] == result_sampnum]:
                    location, time, matrix, fieldid, aocid, spx, spy = df2.loc[x, ['Sampnum', 'Samptime', 'Matrix', 'Fieldid', 'Aocid', 'Sp_x', 'Sp_y']]
                    location, time, matrix, fieldid, aocid, spx, spy = [clean_value(value) for value in (location, time, matrix, fieldid, aocid, spx, spy)]
                    location = site
                    time = pd.to_datetime(time).time()
                    fieldid = standardize_address(conn, porewater_location_table, location, fieldid, address_cache)
                    conn.execute(
                        Update(porewater_data).where(porewater_data.c.Location_Name == location),
                        [{'Sample_Time': time}],
                    )
                    conn.execute(
                        Update(porewater_location_table).where(porewater_location_table.c.Location_Name == location),
                        [{
                            'Matrix': matrix,
                            'Address': fieldid,
                            'AOC': aocid,
                            'X_Coordinate': spx,
                            'Y_Coordinate': spy
                        }],
                    )
            else:
                insert_result(conn, other_data, result_record)
                for x in df2.index[df2['Sampnum'] == result_sampnum]:
                    location, time, matrix, fieldid, aocid, spx, spy = df2.loc[x, ['Sampnum', 'Samptime', 'Matrix', 'Fieldid', 'Aocid', 'Sp_x', 'Sp_y']]
                    location, time, matrix, fieldid, aocid, spx, spy = [clean_value(value) for value in (location, time, matrix, fieldid, aocid, spx, spy)]
                    location = site
                    time = pd.to_datetime(time).time()
                    fieldid = standardize_address(conn, other_location_table, location, fieldid, address_cache)
                    conn.execute(
                        Update(other_data).where(other_data.c.Location_Name == location),
                        [{'Sample_Time': time}],
                    )
                    conn.execute(
                        Update(other_location_table).where(other_location_table.c.Location_Name == location),
                        [{
                            'Matrix': matrix,
                            'Address': fieldid,
                            'AOC': aocid,
                            'X_Coordinate': spx,
                            'Y_Coordinate': spy
                        }],
                    )
            update_progress()

    return db_path