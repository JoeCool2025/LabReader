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

dup_list = []

def clean_value(value):
    if pd.isna(value) or value == '':
        return None
    if hasattr(value, 'item'):
        value = value.item()
    return value

def tsv_reader(file, db, labtype, samp_file):
    global dup_list
    if db == None or db == '':
        db_path = db_maker(file)
    else:
        db_path = db
    df = pd.read_csv(file, sep='\t')
    df2 = pd.read_csv(samp_file, sep='\t')

    engine = create_engine(f'sqlite:///{db_path}')
    metadata_obj = MetaData()
    metadata_obj.create_all(engine)
    gw_location_table = Table('gw_locations', metadata_obj, autoload_with=engine)
    gw_data = Table('gw_results', metadata_obj, autoload_with=engine)
    soil_location_table = Table('soil_locations', metadata_obj, autoload_with=engine)
    soil_data = Table('soil_results', metadata_obj, autoload_with=engine)
    porewater_location_table = Table('porewater_locations', metadata_obj, autoload_with=engine)
    porewater_data = Table('porewater_results', metadata_obj, autoload_with=engine)
    try:
        df.to_sql(name=f"{df.at[0, 'QAQC']}", con=engine)
    except ValueError:
        print("Lab Data already in Selected Database")
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
                    Insert(gw_location_table),
                    [{"Location_Name": site}],
                )
            except exc.IntegrityError:
                dup_list.append(row)

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
            print("The following locations already exist in the database: ")
            for item in dup_list:
                print(item)
        for x in range(0, len(df)):
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
                for x in range(0, len(df2)):
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
                for x in range(0, len(df2)):
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
                        Update(soil_data).where(gw_data.c.Location_Name == location),
                        [{'Sample_Time': time}],
                    )
                    conn.execute(
                        Update(soil_location_table).where(gw_location_table.c.Location_Name == location),
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
                for x in range(0, len(df2)):
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
                        Update(porewater_data).where(gw_data.c.Location_Name == location),
                        [{'Sample_Time': time}],
                    )
                    conn.execute(
                        Update(porewater_location_table).where(gw_location_table.c.Location_Name == location),
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