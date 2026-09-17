import pandas as pd
from sqlalchemy import Table, create_engine, MetaData, select, inspect
import numpy as np
import PySimpleGUI as sg
from col_select import col_choose

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

def export(path, selected_columns=None, mode=None):
    engine = create_engine(f'sqlite:///{path}')
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
    saveloc = sg.popup_get_file('Save As', default_extension='.xlsx', save_as=True, file_types=(('.xlsx', '*.xlsx'),))

    if selected_columns is None or mode is None:
        columns = set()
        for table in (
            gw_data,
            gw_location_table,
            soil_data,
            soil_location_table,
            porewater_data,
            porewater_location_table,
            other_data,
            other_location_table,
        ):
            columns.update(table.c.keys())
        columns, mode = col_choose(list(columns))
    else:
        columns = selected_columns

    if mode == 'Separate':
        string = ''
        for column in columns:
            if column in gw_data.c.keys():
                if column == 'Method_Detection_Limit':
                    string += f'{column} AS MDL, '
                else:
                    string += f'{column}, '
            else:
                continue
        string = string[:-2]
        gwr = pd.read_sql(
            f'SELECT {string} FROM gw_results ',
            con=engine
        )
        string = ''
        for column in columns:
            if column in gw_location_table.c.keys():
                string += f'{column}, '
            else:
                continue
        string = string[:-2]
        gwloc = pd.read_sql(
            f'SELECT {string} FROM gw_locations ',
            con=engine
        )
        string = ''
        for column in columns:
            if column in soil_data.c.keys():
                if column == 'Method_Detection_Limit':
                    string += f'{column} AS MDL, '
                else:
                    string += f'{column}, '
            else:
                continue
        string = string[:-2]
        soilr = pd.read_sql(
            f'SELECT {string} FROM soil_results ',
            con=engine
        )
        string = ''
        for column in columns:
            if column in soil_location_table.c.keys():
                string += f'{column}, '
            else:
                continue
        string = string[:-2]
        soilloc = pd.read_sql(
            f'SELECT {string} FROM soil_locations ',
            con=engine
        )
        string = ''
        for column in columns:
            if column in porewater_data.c.keys():
                if column == 'Method_Detection_Limit':
                    string += f'{column} AS MDL, '
                else:
                    string += f'{column}, '
            else:
                continue
        string = string[:-2]
        porer = pd.read_sql(
            f'SELECT {string} FROM porewater_results ',
            con=engine
        )
        string = ''
        for column in columns:
            if column in porewater_location_table.c.keys():
                string += f'{column}, '
            else:
                continue
        string = string[:-2]
        poreloc = pd.read_sql(
            f'SELECT {string} FROM porewater_locations ',
            con=engine
        )
        string = ''
        for column in columns:
            if column in other_data.c.keys():
                if column == 'Method_Detection_Limit':
                    string += f'{column} AS MDL, '
                else:
                    string += f'{column}, '
            else:
                continue
        string = string[:-2]
        otherr = pd.read_sql(
            f'SELECT {string} FROM other_results ',
            con=engine
        )
        string = ''
        for column in columns:
            if column in other_location_table.c.keys():
                string += f'{column}, '
            else:
                continue
        string = string[:-2]
        otherloc = pd.read_sql(
            f'SELECT {string} FROM other_locations ',
            con=engine
        )
        with pd.ExcelWriter(saveloc) as writer:
            sheets = {
                'Groundwater Data': gwr,
                'Groundwater Locations': gwloc,
                'Soil Data': soilr,
                'Soil Locations': soilloc,
                'Porewater Data': porer,
                'Porewater Locations': poreloc,
                'Other Data': otherr,
                'Other Locations': otherloc
            }
            for sheet_name, dataframe in sheets.items():
                if not dataframe.empty:
                    dataframe.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        string = ''
        for column in columns:
            if column in gw_data.c.keys():
                tab = 'gw_results'
            elif column in gw_location_table.c.keys():
                tab = 'gw_locations'
            else:
                continue
            if column == 'Method_Detection_Limit':
                string += f'{tab}.{column} AS MDL, '
            else:
                string += f'{tab}.{column}, '
        string = string[:-2]
        gw = pd.read_sql(
            f'SELECT {string} FROM gw_results '
            'FULL JOIN gw_locations ON gw_results.Location_Name = gw_locations.Location_Name ',
            con=engine
        )
        string = ''
        for column in columns:
            if column in soil_data.c.keys():
                tab = 'soil_results'
            elif column in soil_location_table.c.keys():
                tab = 'soil_locations'
            else:
                continue
            if column == 'Method_Detection_Limit':
                string += f'{tab}.{column} AS MDL, '
            else:
                string += f'{tab}.{column}, '
        string = string[:-2]
        soil = pd.read_sql(
            f'SELECT {string} FROM soil_results '
            'FULL JOIN soil_locations ON soil_results.Location_Name = soil_locations.Location_Name ',
            con=engine
        )
        string = ''
        for column in columns:
            if column in porewater_data.c.keys():
                tab = 'porewater_results'
            elif column in porewater_location_table.c.keys():
                tab = 'porewater_locations'
            else:
                continue
            if column == 'Method_Detection_Limit':
                string += f'{tab}.{column} AS MDL, '
            else:
                string += f'{tab}.{column}, '
        string = string[:-2]
        pore = pd.read_sql(
            f'SELECT {string} FROM porewater_results '
            'FULL JOIN porewater_locations ON porewater_results.Location_Name = porewater_locations.Location_Name ',
            con=engine
        )
        string = ''
        for column in columns:
            if column in other_data.c.keys():
                tab = 'other_results'
            elif column in other_location_table.c.keys():
                tab = 'other_locations'
            else:
                continue
            if column == 'Method_Detection_Limit':
                string += f'{tab}.{column} AS MDL, '
            else:
                string += f'{tab}.{column}, '
        string = string[:-2]
        other = pd.read_sql(
            f'SELECT {string} FROM other_results '
            'FULL JOIN other_locations ON other_results.Location_Name = other_locations.Location_Name ',
            con=engine
        )

        with pd.ExcelWriter(saveloc) as writer:
            sheets = {
                'Groundwater Data': gw,
                'Soil Data': soil,
                'Porewater Data': pore,
                'Other Data': other,
            }
            for sheet_name, dataframe in sheets.items():
                if not dataframe.empty:
                    dataframe.to_excel(writer, sheet_name=sheet_name, index=False)
    return