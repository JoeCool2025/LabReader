import pandas as pd
import PySimpleGUI as sg
from casn_lookup import casn_search
from sqlalchemy import (
    Insert,
    MetaData,
    Table,
    select,
    create_engine,
    exc
)
from make_db import db_maker
dup_list = []

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
            xcoord = sg.popup_get_text(f'Input X Coordinate for {site}:')
            ycoord = sg.popup_get_text(f'Input Y Coordinate for {site}:')
            long = sg.popup_get_text(f'Input Longitude for {site}:')
            lat = sg.popup_get_text(f'Input Latitude for {site}:')
            if labtype == 'Groundwater':
                layer = sg.popup_get_text(f'Input Layer for {site}:')
                s_tail = sg.popup_get_text(f'Input S for Source, or T for Tail (leave blank if not in use) for {site}:')
                sat_thick = sg.popup_get_text(f'Input Saturated Thickness for {site}:')
                stunit = sg.popup_get_text(f'Input units for Saturated Thickness for {site}:')
                porosity = sg.popup_get_text(f'Input Porosity for {site}:')
                conn.execute(
                    Insert(gw_location_table),
                    [{"X_Coordinate": xcoord,
                      "Y_Coordinate": ycoord,
                      "Longitude": long,
                      "Latitude": lat,
                      "Layer": layer,
                      "Source_Tail": s_tail,
                      "Saturated_Thickness": sat_thick,
                      "Units_of_ST": stunit,
                      "Porosity": porosity}]
                )
            elif labtype == 'Soil':
                thick = sg.popup_get_text(f'Input Thickness for {site}:')
                thickunit = sg.popup_get_text(f'Input units for Thickness for {site}:')
                bulkd = sg.popup_get_text(f'Input Bulk Density for {site}:')
                bulkdunit = sg.popup_get_text(f'Input units for Bulk Density for {site}:')
                perlowk = sg.popup_get_text(f'Input Percentage Low K for {site}:')
                conn.execute(
                    Insert(soil_location_table),
                    [{"X_Coordinate": xcoord,
                      "Y_Coordinate": ycoord,
                      "Longitude": long,
                      "Latitude": lat,
                      "Thickness": thick,
                      "Units_of_Thickness": thickunit,
                      "Bulk_Density": bulkd,
                      "Units_of_Bulk_Density": bulkdunit,
                      "Percent_Low_L": perlowk}]
                )
            else:
                conn.execute(
                    Insert(porewater_location_table),
                    [{"X_Coordinate": xcoord,
                      "Y_Coordinate": ycoord,
                      "Longitude": long,
                      "Latitude": lat}]
                )
            print(labtype)
        if len(dup_list) != 0:
            print("The following locations already exist in the database: ")
            for item in dup_list:
                print(item)
        for x in range(0, len(df)):
            location, analyte_name, casn, date, result, res_unit, mdl = df.loc[x, ['Sampnum', 'Analtparam', 'Cas', 'Sampdate', 'Conc', 'Concunits', 'Mdl']]
            date = pd.to_datetime(date)
            location = location[:-5]
            #try:
                #analyte = casn_search(analyte_name)
                #break
            #except FileNotFoundError:
                #analyte = sg.popup_get_text(f'{analyte_name} not found in CASN Database\nPlease enter CASN for {analyte_name}:', default_text='')
            conn.execute(
                Insert(gw_data),
                [
                    {'Location_Name': location,
                    'Analyte': analyte_name,
                    'CASN': casn,
                    'Sample_Date': date,
                    'Result': result,
                    'Result_Unit': res_unit,
                    'Method_Detection_Limit': mdl},
                ],
            )

    return