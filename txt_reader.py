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

def tsv_reader(file, db):
    global dup_list
    if db == None:
        db_path = db_maker(file)
    else:
        db_path = db
    df = pd.read_csv(file, sep='\t')    

    engine = create_engine(f'sqlite:///{db_path}')
    #engine = create_engine('sqlite:///:memory:')
    metadata_obj = MetaData()
    metadata_obj.create_all(engine)
    gw_location_table = Table('gw_locations', metadata_obj, autoload_with=engine)
    gw_data = Table('gw_results', metadata_obj, autoload_with=engine)
    try:
        df.to_sql(name=f"{df.at[0, 'QAQC']}", con=engine)
    except ValueError:
        print("Lab Data already in Selected Database")
        return
    with engine.begin() as conn:
        for row in df.loc[:, 'Sampnum'].unique():
            try:
                conn.execute(
                    Insert(gw_location_table),
                    [{"Location_Name": row}],
                )
            except exc.IntegrityError:
                dup_list.append(row)
        if len(dup_list) != 0:
            print("The following locations already exist in the database: ")
            for item in dup_list:
                print(item)
        for x in range(0, len(df)):
            location, analyte_name, date, result, res_unit, mdl = df.loc[x, ['Sampnum', 'Analtparam', 'Sampdate', 'Conc', 'Concunits', 'Mdl']]
            date = pd.to_datetime(date)
            while True:
                try:
                    analyte = casn_search(analyte_name)
                    break
                except FileNotFoundError:
                    analyte_name = sg.popup_get_text(f'{analyte_name} not found in CASN Database\nPlease enter CASN for {analyte_name}:', default_text='')
            conn.execute(
                Insert(gw_data),
                [
                    {'Location Name': location,
                    'Analyte': analyte,
                    'Sample Date': date,
                    'Result': result,
                    'Result Unit': res_unit,
                    'Method Detection Limit': mdl},
                ],
            )

    return