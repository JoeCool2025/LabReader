import PySimpleGUI as sg
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, MetaData, Update, Insert, Table

# Example update_info nesting:
# {'gwdata': {'id': {*insert updated data in this dict*}}
#  'gw_location': {'Location_Name'{*insert updated location data in this dict*}}}

def dbedit(engine, update_info):
    with engine.begin() as conn:
        for table, loc in update_info.items():
            for key, val in loc.items():
                try:
                    for k, v in val.items():
                        if str(table) in ['gw_results', 'soil_results', 'porewater_results']:
                            try:
                                conn.execute(Update(table).where(table.c.id == key),{k: v})
                            except Exception as e:
                                print(e)
                        elif str(table) in ['gw_locations', 'soil_locations', 'porewater_locations']:
                            try:
                                conn.execute(Update(table).where(table.c.Location_Name == key),{k: v})
                            except Exception as e:
                                print(e)
                        else:
                            sg.popup_quick_message(f"{table} not recognized as valid table name")
                except:
                    sg.popup_quick_message("oops")

def parseedit(edits, db_path):
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

    edit_dict = {}
    for e in edits:
        if e["table"] == '-GWDATA-':
            edit_dict[gw_data] = {int(e["row"]): {e["col"]: e["value"]}}
        elif e["table"] == '-GWLOC-':
            edit_dict[gw_location_table] = {e["row"]: {e["col"]: e["value"]}}
        elif e["table"] == '-SOILDATA-':
            edit_dict[soil_data] = {int(e["row"]): {e["col"]: e["value"]}}
        elif e["table"] == '-SOILLOC-':
            edit_dict[soil_location_table] = {e["row"]: {e["col"]: e["value"]}}
        elif e["table"] == '-POREDATA-':
            edit_dict[porewater_data] = {int(e["row"]): {e["col"]: e["value"]}}
        elif e["table"] == '-PORELOC-':
            edit_dict[porewater_location_table] = {e["row"]: {e["col"]: e["value"]}}
        elif e["table"] == '-OTHERDATA-':
            edit_dict[other_data] = {int(e["row"]): {e["col"]: e["value"]}}
        elif e["table"] == '-OTHERLOC-':
            edit_dict[other_location_table] = {(e["row"]): {e["col"]: e["value"]}}
        else:
            sg.popup_quick_message(f'{e["table"]} not recognized as valid table name')

    dbedit(engine, edit_dict)