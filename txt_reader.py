import pandas as pd
import PySimpleGUI as sg
from casn_lookup import casn_search
from sqlalchemy import (
    Insert,
    MetaData,
    Table,
    select,
    create_engine,
    exc,
    Update
)
from make_db import db_maker
from type_selection import matrixselection

def clean_value(value):
    if pd.isna(value) or value == '':
        return None
    if hasattr(value, 'item'):
        value = value.item()
    return value

def findlabtype(df):
    dict = {}
    loclist = []
    for location in df.loc[:, 'Sampnum'].unique():
        loclist.append(location)
    recognized_matrices = {
        'groundwater': 'Groundwater',
        'ground water': 'Groundwater',
        'soil': 'Soil',
        'porewater': 'Porewater',
        'pore water': 'Porewater',
    }
    matrix_values = df.loc[:, 'Matrix'].unique()
    invalid_matrix_found = any(
        not isinstance(matrix, str) or matrix.strip().lower() not in recognized_matrices
        for matrix in matrix_values
    )
    if not invalid_matrix_found:
        normalized_matrices = {
            location: recognized_matrices[matrix.strip().lower()]
            for location, matrix in zip(df['Sampnum'], df['Matrix'])
        }
        unique_matrices = set(normalized_matrices.values())
        if len(unique_matrices) == 1:
            return 1, unique_matrices.pop()
        return 2, normalized_matrices

    layout = [
        [sg.Text('Please select Groundwater sites')],
        [sg.Listbox(values=loclist, select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE, expand_x=True, size=(20,6), key='-GWSEL-')],
        [sg.Button('Confirm Selection')]
    ]
    layout2 = [
        [sg.Text('Please select Soil sites')],
        [sg.Listbox(values=loclist, select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE, expand_x=True, size=(20,6), key='-SOILSEL-')],
        [sg.Button('Confirm Selection')]
    ]
    layout3 = [
        [sg.Text('Please select Porewater sites')],
        [sg.Listbox(values=loclist, select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE, expand_x=True, size=(20,6), key='-PORESEL-')],
        [sg.Button('Confirm Selection')]
    ]
    matrix = matrixselection()
    if matrix == 'Mixed':
        gwwin = sg.Window('Groundwater sites', layout, enable_close_attempted_event=True)
        while True:
            gwevent, gwvalues = gwwin.read()

            if gwevent == 'Confirm Selection':
                gw = gwvalues['-GWSEL-']
                for location in gw:
                    dict[location] = 'Groundwater'
                    loclist.remove(location)
                gwwin.close()
                break
            if gwevent == sg.WIN_CLOSE_ATTEMPTED_EVENT:
                sg.popup_quick_message('Please Select Groundwater Locations')
                continue

        soilwin = sg.Window('Soil sites', layout2, enable_close_attempted_event=True)
        if len(loclist) <= 0:
            return 2, dict

        while True:
            soilevent, soilvalues = soilwin.read()

            if soilevent == 'Confirm Selection':
                soil = soilvalues['-SOILSEL-']
                for location in soil:
                    dict[location] = 'Soil'
                    loclist.remove(location)
                soilwin.close()
                break
            if soilevent == sg.WIN_CLOSE_ATTEMPTED_EVENT:
                sg.popup_quick_message('Please Select Soil Locations')
                continue

        if len(loclist) <= 0:
            return 2, dict

        porewin = sg.Window('Porewater sites', layout3, enable_close_attempted_event=True)
        while True:
            poreevent, porevalues = porewin.read()

            if poreevent == 'Confirm Selection':
                pore = porevalues['-PORESEL-']
                for location in pore:
                    dict[location] = 'Porewater'
                    loclist.remove(location)
                porewin.close()
                break
            if poreevent == sg.WIN_CLOSE_ATTEMPTED_EVENT:
                sg.popup_quick_message('Please Select Porewater Locations')
                continue

        return 2, dict
    return 1, matrix

def tsv_reader(file, db, samp_file):
    dup_list = []
    if db == None or db == '':
        db_path = db_maker(file)
    else:
        db_path = db
    df = pd.read_csv(file, sep='\t') #read hzresult file
    df2 = pd.read_csv(samp_file, sep='\t') #read hzsample file
    v, m = findlabtype(df2)
    df2['Matrix'] = df2['Matrix'].astype(object)
    if v == 1:
        for x in range(0, len(df2)):
            df2.at[x, 'Matrix'] = m
    elif v == 2:
        for key in m.keys():
            df2.loc[df2['Sampnum'] == key, 'Matrix'] = m[key]
    mapping = df2.set_index('Sampnum')['Matrix']
    df['Matrix'] = df['Sampnum'].map(mapping)

    engine = create_engine(f'sqlite:///{db_path}')
    metadata_obj = MetaData()
    metadata_obj.create_all(engine)
    gw_location_table = Table('gw_locations', metadata_obj, autoload_with=engine)
    gw_data = Table('gw_results', metadata_obj, autoload_with=engine)
    soil_location_table = Table('soil_locations', metadata_obj, autoload_with=engine)
    soil_data = Table('soil_results', metadata_obj, autoload_with=engine)
    porewater_location_table = Table('porewater_locations', metadata_obj, autoload_with=engine)
    porewater_data = Table('porewater_results', metadata_obj, autoload_with=engine)

    location_tables = {
        'Groundwater': gw_location_table,
        'Soil': soil_location_table,
        'Porewater': porewater_location_table,
    }

    try:
        df.to_sql(name=f"{df.at[0, 'QAQC']}", con=engine)
    except ValueError:
        sg.popup_quick_message('Lab Data already in Selected Database')
        return
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

    with engine.begin() as conn:
        for row in df.loc[:, 'Sampnum'].unique():
            labtype = mapping.get(row)
            try:
                sampdate = pd.to_datetime(df.loc[df['Sampnum'] == row, 'Sampdate'].iloc[0])
            except IndexError:
                sampdate = pd.to_datetime(sg.popup_get_date(title=f'No Date Found. Please provide date for {row}:'))
            if isinstance(row, str) and len(row) >= 5 and row[-5] == '-' and row[-4:].isdigit():
                if row[:2].lower() == 'tb' or row[:2].lower() == 'fb' or row[:3].lower() == 'dup':
                    site = row[:-5] + '-' + sampdate.strftime("%m%Y")
                else:
                    site = row[:-5]
            else:
                if row[:2].lower() == 'tb' or row[:2].lower() == 'fb' or row[:3].lower() == 'dup':
                    site = row + '-' + sampdate.strftime("%m%Y")
                else:
                    site = row
            try:
                conn.execute(
                    Insert(location_tables[labtype]),
                    [{"Location_Name": site}],
                )
            except exc.IntegrityError:
                dup_list.append(row)
                continue

            xcoord = None
            ycoord = None
            long = None
            lat = None

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
                        'Longitude': long,
                        'Latitude': lat,
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
                        'Longitude': long,
                        'Latitude': lat,
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
                        'Longitude': long,
                        'Latitude': lat,
                    }]
                )
            update_progress()
        if len(dup_list) != 0:
            dup_layout = [[sg.Text('The following locations already exist in the database: ')]]
            for item in dup_list:
                dup_layout.append([sg.Text(f'{item}')])
            dup_win = sg.Window('Duplicate Locations', layout=dup_layout, auto_close=True, auto_close_duration=5)
            dup_win.read()
        for x in range(0, len(df)):
            result_sampnum = df.loc[x, 'Sampnum']
            labtype = clean_value(df.loc[x, 'Matrix'])
            location, analyte_name, casn, date, result, res_unit, mdl, flag = df.loc[x, ['Sampnum', 'Analtparam', 'Cas', 'Sampdate', 'Conc', 'Concunits', 'Mdl', 'Qaqual']]
            date = pd.to_datetime(date)
            if isinstance(location, str) and len(location) >= 5 and location[-5] == '-' and location[-4:].isdigit():
                location = location[:-5]
            if location[:2].lower() == 'tb' or location[:2].lower() == 'fb' or location[:3].lower() == 'dup':
                location += '-' + date.strftime("%m%Y")
            if result.lower() == 'nd':
                result = None
            detect = True
            trace = False
            dup = False
            if flag == 'U':
                detect = False
            if flag == 'J' or flag == 'TR':
                trace = True
            if location[:3] == 'DUP':
                dup = True
            if labtype == 'Groundwater':
                conn.execute(
                    Insert(gw_data),
                    [
                        {'Location_Name': location,
                        'Analyte': analyte_name,
                        'CASN': casn,
                        'Sample_Date': date,
                        'Result': result,
                        'Result_Unit': res_unit,
                        'Method_Detection_Limit': mdl,
                        'Flag': flag,
                        'Detect': detect,
                        'Trace': trace,
                        'Duplicate': dup,
                        'Exclude': False},
                    ],
                )
                if analyte_name[-5:] == 'TOTAL':
                    conn.execute(
                        Update(gw_data)
                        .where(gw_data.c.Analyte == analyte_name),
                        [{'Chem_Group': 'TOT'},],
                    )
                for x in df2.index[df2['Sampnum'] == result_sampnum]:
                    location, time, matrix, fieldid, aocid, latdeg, latmin, latsec, londeg, lonmin, lonsec, spx, spy, depthtop, depthbot, groundel, wellel, screentop, screenbot = df2.loc[x, ['Sampnum', 'Samptime', 'Matrix', 'Fieldid', 'Aocid', 'Lat_degree', 'Lat_minute', 'Lat_second', 'Lon_degree', 'Lon_minute', 'Lon_second', 'Sp_x', 'Sp_y', 'Depth_top', 'Depth_botm', 'GroundElev', 'Well_elev', 'Screentop', 'Screenbot']]
                    location, time, matrix, fieldid, aocid, latdeg, latmin, latsec, londeg, lonmin, lonsec, spx, spy, depthtop, depthbot, groundel, wellel, screentop, screenbot = [clean_value(value) for value in (location, time, matrix, fieldid, aocid, latdeg, latmin, latsec, londeg, lonmin, lonsec, spx, spy, depthtop, depthbot, groundel, wellel, screentop, screenbot)]
                    time = pd.to_datetime(time).time()
                    if latdeg is None or latmin is None or latsec is None:
                        lat = None
                    else:
                        lat = f'{latdeg}\u00b0 {latmin}\u2032 {latsec}\u2033'
                    if londeg is None or lonmin is None or lonsec is None:
                        long = None
                    else:
                        long = f'{londeg}\u00b0 {lonmin}\u2032 {lonsec}\u2033'
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
                            'Latitude': lat,
                            'Longitude': long,
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
                conn.execute(
                    Insert(soil_data),
                    [
                        {'Location_Name': location,
                        'Analyte': analyte_name,
                        'CASN': casn,
                        'Sample_Date': date,
                        'Result': result,
                        'Result_Unit': res_unit,
                        'Method_Detection_Limit': mdl,
                        'Flag': flag,
                        'Detect': detect,
                        'Trace': trace,
                        'Duplicate': dup,
                        'Exclude': False},
                    ],
                )
                if analyte_name[-5:] == 'TOTAL' or analyte_name[:5]:
                    conn.execute(
                        Update(soil_data)
                        .where(soil_data.c.Analyte == analyte_name),
                        [{'Chem_Group': 'TOT'},],
                    )
                for x in df2.index[df2['Sampnum'] == result_sampnum]:
                    location, time, matrix, fieldid, aocid, latdeg, latmin, latsec, londeg, lonmin, lonsec, spx, spy = df2.loc[x, ['Sampnum', 'Samptime', 'Matrix', 'Fieldid', 'Aocid', 'Lat_degree', 'Lat_minute', 'Lat_second', 'Lon_degree', 'Lon_minute', 'Lon_second', 'Sp_x', 'Sp_y']]
                    location, time, matrix, fieldid, aocid, latdeg, latmin, latsec, londeg, lonmin, lonsec, spx, spy = [clean_value(value) for value in (location, time, matrix, fieldid, aocid, latdeg, latmin, latsec, londeg, lonmin, lonsec, spx, spy)]
                    time = pd.to_datetime(time).time()
                    if latdeg is None or latmin is None or latsec is None:
                        lat = None
                    else:
                        lat = f'{latdeg}\u00b0 {latmin}\u2032 {latsec}\u2033'
                    if londeg is None or lonmin is None or lonsec is None:
                        long = None
                    else:
                        long = f'{londeg}\u00b0 {lonmin}\u2032 {lonsec}\u2033'
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
                            'Latitude': lat,
                            'Longitude': long,
                            'X_Coordinate': spx,
                            'Y_Coordinate': spy
                        }],
                    )
            elif labtype == 'Porewater':
                conn.execute(
                    Insert(porewater_data),
                    [
                        {'Location_Name': location,
                        'Analyte': analyte_name,
                        'CASN': casn,
                        'Sample_Date': date,
                        'Result': result,
                        'Result_Unit': res_unit,
                        'Method_Detection_Limit': mdl,
                        'Flag': flag,
                        'Detect': detect,
                        'Trace': trace,
                        'Duplicate': dup,
                        'Exclude': False},
                    ]
                )
                if analyte_name[-5:] == 'TOTAL':
                    conn.execute(
                        Update(porewater_data)
                        .where(porewater_data.c.Analyte == analyte_name),
                        [{'Chem_Group': 'TOT'},],
                    )
                for x in df2.index[df2['Sampnum'] == result_sampnum]:
                    location, time, matrix, fieldid, aocid, latdeg, latmin, latsec, londeg, lonmin, lonsec, spx, spy = df2.loc[x, ['Sampnum', 'Samptime', 'Matrix', 'Fieldid', 'Aocid', 'Lat_degree', 'Lat_minute', 'Lat_second', 'Lon_degree', 'Lon_minute', 'Lon_second', 'Sp_x', 'Sp_y']]
                    location, time, matrix, fieldid, aocid, latdeg, latmin, latsec, londeg, lonmin, lonsec, spx, spy = [clean_value(value) for value in (location, time, matrix, fieldid, aocid, latdeg, latmin, latsec, londeg, lonmin, lonsec, spx, spy)]
                    time = pd.to_datetime(time).time()
                    if latdeg is None or latmin is None or latsec is None:
                        lat = None
                    else:
                        lat = f'{latdeg}\u00b0 {latmin}\u2032 {latsec}\u2033'
                    if londeg is None or lonmin is None or lonsec is None:
                        long = None
                    else:
                        long = f'{londeg}\u00b0 {lonmin}\u2032 {lonsec}\u2033'
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
                            'Latitude': lat,
                            'Longitude': long,
                            'X_Coordinate': spx,
                            'Y_Coordinate': spy
                        }],
                    )
            update_progress()

    progress_window.close()
    return