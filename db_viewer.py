import pandas as pd
from sqlalchemy import Table, create_engine, MetaData, select
import numpy as np

def db2df(path, columns=['Location_Name', 'Analyte', 'CASN', 'Sample_Date', 'Result', 'Result_Unit', 'Method_Detection_Limit']):
    if path == None or path == '':
        raise Exception("No Database Chosen")
    engine = create_engine(f'sqlite:///{path}')
    metadata_obj = MetaData()
    metadata_obj.create_all(engine)
    gw_location_table = Table('gw_locations', metadata_obj, autoload_with=engine)
    gw_data = Table('gw_results', metadata_obj, autoload_with=engine)
    soil_location_table = Table('soil_locations', metadata_obj, autoload_with=engine)
    soil_data = Table('soil_results', metadata_obj, autoload_with=engine)
    porewater_location_table = Table('porewater_locations', metadata_obj, autoload_with=engine)
    porewater_data = Table('porewater_results', metadata_obj, autoload_with=engine)

    gw = []
    soil = []
    pore = []
    
    for column in columns:
        if column == 'Method_Detection_Limit':
            stmt = pd.read_sql("SELECT Method_Detection_Limit AS MDL FROM gw_results", con=engine)
        else:
            stmt = pd.read_sql(f"SELECT {column} FROM gw_results", con=engine)
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
    for column in columns:
        if column == 'Method_Detection_Limit':
            stmt = pd.read_sql("SELECT Method_Detection_Limit AS MDL FROM soil_results", con=engine)
        else:
            stmt = pd.read_sql(f"SELECT {column} FROM soil_results", con=engine)
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
    for column in columns:
        if column == 'Method_Detection_Limit':
            stmt = pd.read_sql("SELECT Method_Detection_Limit AS MDL FROM porewater_results", con=engine)
        else:
            stmt = pd.read_sql(f"SELECT {column} FROM porewater_results", con=engine)
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
    return gw, soil, pore

#try:
    #db2df('C:\\Users\\ICohen\\Documents\\LabReader\\Databases\\UB-WALDWICK.db')
#except Exception as e:
    #print(f"oops: {e}")