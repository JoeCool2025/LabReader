import pandas as pd
from sqlalchemy import Table, create_engine, MetaData, select, inspect
import numpy as np
import PySimpleGUI as sg

def clean_database_value(value):
    if pd.isna(value):
        return None
    if isinstance(value, bytes):
        try:
            text_value = value.decode('utf-8')
            if text_value.isprintable():
                return text_value
        except UnicodeDecodeError:
            pass
        return int.from_bytes(value, byteorder='little')
    return value

def export(path, user_col=[]):
    engine = create_engine(f'sqlite:///{path}')
    metadata_obj = MetaData()
    metadata_obj.create_all(engine)
    gw_location_table = Table('gw_locations', metadata_obj, autoload_with=engine)
    gw_data = Table('gw_results', metadata_obj, autoload_with=engine)
    soil_location_table = Table('soil_locations', metadata_obj, autoload_with=engine)
    soil_data = Table('soil_results', metadata_obj, autoload_with=engine)
    porewater_location_table = Table('porewater_locations', metadata_obj, autoload_with=engine)
    porewater_data = Table('porewater_results', metadata_obj, autoload_with=engine)
    database_inspector = inspect(engine)

    gw = []
    gwloc = []
    soil = []
    soilloc = []
    pore = []
    poreloc = []
    other = []
    otherloc = []
    columns = ['Location_Name', 'Analyte', 'CASN', 'Sample_Date', 'Sample_Time', 'Result', 'Result_Unit', 'Method_Detection_Limit']
    columns += user_col
    
    for column in columns:
        if column == 'Method_Detection_Limit':
            stmt = pd.read_sql(
                "SELECT Method_Detection_Limit AS MDL FROM gw_results "
                "ORDER BY CASE WHEN INSTR(Location_Name, '-')>0 "
                "THEN CAST(SUBSTR(Location_Name, INSTR(Location_NAME, '-')+1) AS INTEGER) END, Location_Name, id",
                con=engine
            )
        else:
            stmt = pd.read_sql(
                f"SELECT {column} FROM gw_results "
                "ORDER BY CASE WHEN INSTR(Location_Name,'-')>0 "
                "THEN CAST(SUBSTR(Location_Name, INSTR(Location_Name,'-')+1) AS INTEGER) END, Location_Name, id",
                con=engine
            )
        for i in range(0, len(stmt)):
            if type(stmt.iloc[i, 0]) == np.float64:
                try:
                    gw[i].append(float(stmt.iloc[i, 0]))
                except:
                    gw.append([float(stmt.iloc[i, 0])])
            elif type(stmt.iloc[i, 0]) == np.integer:
                try:
                    gw[i].append(int(stmt.iloc[i, 0]))
                except:
                    gw.append([int(stmt.iloc[i, 0])])
            else:
                try:
                    gw[i].append(stmt.iloc[i, 0])
                except:
                    gw.append([stmt.iloc[i, 0]])
    stmt = pd.read_sql(
        "SELECT * FROM gw_locations "
        "ORDER BY CASE WHEN INSTR(Location_Name,'-')>0 "
        "THEN CAST(SUBSTR(Location_Name, INSTR(Location_Name,'-')+1) AS INTEGER) END, Location_Name",
        con=engine
    )  
    for i in range(0, len(stmt)):
        gwloc.append([clean_database_value(value) for value in stmt.iloc[i].tolist()])
    for column in columns:
        if column == 'Method_Detection_Limit':
            stmt = pd.read_sql(
                "SELECT Method_Detection_Limit AS MDL FROM soil_results "
                "ORDER BY CASE WHEN INSTR(Location_Name, '-')>0 "
                "THEN CAST(SUBSTR(Location_Name, INSTR(Location_Name, '-')+1) AS INTEGER) END, Location_Name, id",
                con=engine
            )
        else:
            stmt = pd.read_sql(
                f"SELECT {column} FROM soil_results "
                "ORDER BY CASE WHEN INSTR(Location_Name,'-')>0 "
                "THEN CAST(SUBSTR(Location_Name, INSTR(Location_Name,'-')+1) AS INTEGER) END, Location_Name, id",
                con=engine
            )
        for i in range(0, len(stmt)):
            if type(stmt.iloc[i, 0]) == np.float64:
                try:
                    soil[i].append(float(stmt.iloc[i, 0]))
                except:
                    soil.append([float(stmt.iloc[i, 0])])
            elif type(stmt.iloc[i, 0]) == np.integer:
                try:
                    soil[i].append(int(stmt.iloc[i, 0]))
                except:
                    soil.append([int(stmt.iloc[i, 0])])
            else:
                try:
                    soil[i].append(stmt.iloc[i, 0])
                except:
                    soil.append([stmt.iloc[i, 0]])
    stmt = pd.read_sql(
        "SELECT * FROM soil_locations "
        "ORDER BY CASE WHEN INSTR(Location_Name,'-')>0 "
        "THEN CAST(SUBSTR(Location_Name, INSTR(Location_Name,'-')+1) AS INTEGER) END, Location_Name",
        con=engine
    )
    for i in range(0, len(stmt)):
        soilloc.append([clean_database_value(value) for value in stmt.iloc[i].tolist()])
    for column in columns:
        if column == 'Method_Detection_Limit':
            stmt = pd.read_sql(
                "SELECT Method_Detection_Limit AS MDL FROM porewater_results "
                "ORDER BY CASE WHEN INSTR(Location_Name, '-')>0 "
                "THEN CAST(SUBSTR(Location_Name, INSTR(Location_Name, '-')+1) AS INTEGER) END, Location_Name, id",
                con=engine
            )
        else:
            stmt = pd.read_sql(
                f"SELECT {column} FROM porewater_results "
                "ORDER BY CASE WHEN INSTR(Location_Name,'-')>0 "
                "THEN CAST(SUBSTR(Location_Name, INSTR(Location_Name,'-')+1) AS INTEGER) END, Location_Name, id",
                con=engine
            )
        for i in range(0, len(stmt)):
            if type(stmt.iloc[i, 0]) == np.float64:
                try:
                    pore[i].append(float(stmt.iloc[i, 0]))
                except:
                    pore.append([float(stmt.iloc[i, 0])])
            elif type(stmt.iloc[i, 0]) == np.integer:
                try:
                    pore[i].append(int(stmt.iloc[i, 0]))
                except:
                    pore.append([int(stmt.iloc[i, 0])])
            else:
                try:
                    pore[i].append(stmt.iloc[i, 0])
                except:
                    pore.append([stmt.iloc[i, 0]])
    stmt = pd.read_sql(
        "SELECT * FROM porewater_locations "
        "ORDER BY CASE WHEN INSTR(Location_Name,'-')>0 "
        "THEN CAST(SUBSTR(Location_Name, INSTR(Location_Name,'-')+1) AS INTEGER) END, Location_Name",
        con=engine
    )
    for i in range(0, len(stmt)):
        poreloc.append([clean_database_value(value) for value in stmt.iloc[i].tolist()])
    if database_inspector.has_table('other_results'):
        for column in columns:
            selected_column = 'Method_Detection_Limit' if column == 'Method_Detection_Limit' else column
            alias = 'MDL' if column == 'Method_Detection_Limit' else column
            stmt = pd.read_sql(
                f"SELECT {selected_column} AS {alias} FROM other_results "
                "ORDER BY CASE WHEN INSTR(Location_Name,'-')>0 "
                "THEN CAST(SUBSTR(Location_Name, INSTR(Location_Name,'-')+1) AS INTEGER) END, Location_Name, id",
                con=engine
            )
            for i in range(0, len(stmt)):
                value = clean_database_value(stmt.iloc[i, 0])
                try:
                    other[i].append(value)
                except IndexError:
                    other.append([value])
    if database_inspector.has_table('other_locations'):
        stmt = pd.read_sql(
            "SELECT * FROM other_locations "
            "ORDER BY CASE WHEN INSTR(Location_Name,'-')>0 "
            "THEN CAST(SUBSTR(Location_Name, INSTR(Location_Name,'-')+1) AS INTEGER) END, Location_Name",
            con=engine
        )
        for i in range(0, len(stmt)):
            otherloc.append([clean_database_value(value) for value in stmt.iloc[i].tolist()])
    gwdf = pd.DataFrame(gw, columns=columns)
    gwlocdf = pd.DataFrame(gwloc, columns=gw_location_table.c.keys())
    soildf = pd.DataFrame(soil, columns=columns)
    soillocdf = pd.DataFrame(soilloc, columns=soil_location_table.c.keys())
    poredf = pd.DataFrame(pore, columns=columns)
    porelocdf = pd.DataFrame(poreloc, columns=porewater_location_table.c.keys())
    otherdf = pd.DataFrame(other, columns=columns)
    otherloc_columns = ['Location_Name', 'X_Coordinate', 'Y_Coordinate', 'Matrix', 'Address', 'AOC']
    otherlocdf = pd.DataFrame(otherloc, columns=otherloc_columns)
    saveloc = sg.popup_get_file('Save As', default_extension='.xlsx', save_as=True, file_types=(('.xlsx', '*.xlsx'),))
    if not saveloc:
        return
    with pd.ExcelWriter(saveloc) as writer:
        sheets = {
            'Groundwater Data': gwdf,
            'Groundwater Locations': gwlocdf,
            'Soil Data': soildf,
            'Soil Locations': soillocdf,
            'Porewater Data': poredf,
            'Porewater Locations': porelocdf,
            'Other Data': otherdf,
            'Other Locations': otherlocdf,
        }
        for sheet_name, dataframe in sheets.items():
            if not dataframe.empty:
                dataframe.to_excel(writer, sheet_name=sheet_name, index=False)
    return