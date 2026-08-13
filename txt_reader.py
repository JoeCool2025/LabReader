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


def _safe_popup_value(prompt, default=None, allow_blank=True):
    default_text = '' if default is None else str(default)
    value = sg.popup_get_text(prompt, default_text=default_text)
    if value is None:
        return default if default is not None else None
    value = value.strip()
    if not value and allow_blank:
        return default if default is not None else None
    return value


def _safe_popup_float(prompt, default=None):
    while True:
        value = _safe_popup_value(prompt, default=default, allow_blank=True)
        if value is None or value == '':
            return None
        try:
            return float(value)
        except ValueError:
            sg.popup_error(f'{prompt} must be a number. Please try again.')


def _safe_popup_s_tail(prompt, default=None):
    while True:
        value = _safe_popup_value(prompt, default=default, allow_blank=True)
        if value is None or value == '':
            return None
        normalized = value.strip().upper()
        if normalized in {'S', 'T'}:
            return normalized
        sg.popup_error("Source/Tail must be 'S', 'T', or blank. Please try again.")


def tsv_reader(file, db, labtype):
    global dup_list
    if db == None:
        db_path = db_maker(file)
    else:
        db_path = db
    df = pd.read_csv(file, sep='\t')    

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
    with engine.begin() as conn:
        for row in df.loc[:, 'Sampnum'].unique():
            site = row[:-5]
            try:
                conn.execute(
                    Insert(gw_location_table),
                    [{"Location_Name": site}],
                )
            except exc.IntegrityError:
                dup_list.append(row)

            xcoord = _safe_popup_float(f'Input X Coordinate for {site}:')
            ycoord = _safe_popup_float(f'Input Y Coordinate for {site}:')
            long = _safe_popup_value(f'Input Longitude for {site}:', allow_blank=True)
            lat = _safe_popup_value(f'Input Latitude for {site}:', allow_blank=True)

            if labtype == 'Groundwater':
                layer = _safe_popup_value(f'Input Layer for {site}:', allow_blank=True)
                s_tail = _safe_popup_s_tail(
                    f'Input S for Source, or T for Tail (leave blank if not in use) for {site}:',
                    default=None,
                )
                sat_thick = _safe_popup_float(f'Input Saturated Thickness for {site}:')
                stunit = _safe_popup_value(f'Input units for Saturated Thickness for {site}:', allow_blank=True)
                porosity = _safe_popup_float(f'Input Porosity for {site}:')
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
                thick = _safe_popup_float(f'Input Thickness for {site}:')
                thickunit = _safe_popup_value(f'Input units for Thickness for {site}:', allow_blank=True)
                bulkd = _safe_popup_float(f'Input Bulk Density for {site}:')
                bulkdunit = _safe_popup_value(f'Input units for Bulk Density for {site}:', allow_blank=True)
                perlowk = _safe_popup_float(f'Input Percentage Low K for {site}:')
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
        if len(dup_list) != 0:
            print("The following locations already exist in the database: ")
            for item in dup_list:
                print(item)
        for x in range(0, len(df)):
            location, analyte_name, casn, date, result, res_unit, mdl, flag = df.loc[x, ['Sampnum', 'Analtparam', 'Cas', 'Sampdate', 'Conc', 'Concunits', 'Mdl', 'Qaqual']]
            date = pd.to_datetime(date)
            location = location[:-5]
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

    return