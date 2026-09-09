import pandas as pd
from sqlalchemy import Table, create_engine, MetaData, inspect


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


def load_result_rows(engine, table_name, columns):
    selected_columns = ', '.join(
        'Method_Detection_Limit AS MDL' if column == 'Method_Detection_Limit' else column
        for column in columns
    )
    stmt = pd.read_sql(
        f"SELECT {selected_columns} FROM {table_name} "
        "ORDER BY CASE WHEN INSTR(Location_Name,'-')>0 "
        "THEN CAST(SUBSTR(Location_Name, INSTR(Location_Name,'-')+1) AS INTEGER) END, "
        "Location_Name, id",
        con=engine,
    )
    return stmt.to_numpy(dtype=object).tolist()


def load_location_rows(engine, table_name):
    stmt = pd.read_sql(
        f"SELECT * FROM {table_name} "
        "ORDER BY CASE WHEN INSTR(Location_Name,'-')>0 "
        "THEN CAST(SUBSTR(Location_Name, INSTR(Location_Name,'-')+1) AS INTEGER) END, Location_Name",
        con=engine,
    )
    return [
        [clean_database_value(value) for value in row]
        for row in stmt.itertuples(index=False, name=None)
    ]


def db2df(path):
    if path == None or path == '':
        raise Exception("No Database Chosen")
    engine = create_engine(f'sqlite:///{path}')
    metadata_obj = MetaData()
    metadata_obj.create_all(engine)
    Table('gw_locations', metadata_obj, autoload_with=engine)
    Table('soil_locations', metadata_obj, autoload_with=engine)
    Table('porewater_locations', metadata_obj, autoload_with=engine)
    database_inspector = inspect(engine)

    columns = [
        'id', 'Location_Name', 'Analyte', 'CASN', 'Sample_Date', 'Sample_Time',
        'Result', 'Result_Unit', 'Method_Detection_Limit', 'Flag', 'Detect',
        'Trace', 'Duplicate', 'Exclude', 'Chem_Group'
    ]
    gw = load_result_rows(engine, 'gw_results', columns)
    gwloc = load_location_rows(engine, 'gw_locations')
    soil = load_result_rows(engine, 'soil_results', columns)
    soilloc = load_location_rows(engine, 'soil_locations')
    pore = load_result_rows(engine, 'porewater_results', columns)
    poreloc = load_location_rows(engine, 'porewater_locations')
    other = []
    otherloc = []

    if database_inspector.has_table('other_results'):
        other = load_result_rows(engine, 'other_results', columns)
    if database_inspector.has_table('other_locations'):
        otherloc = load_location_rows(engine, 'other_locations')

    for row in range(0, len(gw)):
        gw[row] = gw[row][1:]
    for row in range(0, len(soil)):
        soil[row] = soil[row][1:]
    for row in range(0, len(pore)):
        pore[row] = pore[row][1:]
    for row in range(0, len(other)):
        other[row] = other[row][1:]
    return gw, gwloc, soil, soilloc, pore, poreloc, other, otherloc
