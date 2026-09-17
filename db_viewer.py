import pandas as pd
from sqlalchemy import Table, create_engine, MetaData, inspect
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


def display_name(column):
    return 'MDL' if column == 'Method_Detection_Limit' else column


def column_ownership(columns, result_table, location_table):
    result_columns = set(result_table.c.keys())
    location_columns = set(location_table.c.keys())
    return {
        column: {
            'result': column in result_columns,
            'location': column in location_columns,
        }
        for column in columns
    }


def select_expression(column, result_table, location_table, ownership, unified, source):
    result_has_column = ownership[column]['result']
    location_has_column = ownership[column]['location']
    output_name = display_name(column)

    if unified and result_has_column and location_has_column:
        expression = (
            f'COALESCE({result_table.name}.{column}, '
            f'{location_table.name}.{column})'
        )
    elif result_has_column and source == 'result':
        expression = f'{result_table.name}.{column}'
    elif location_has_column and source == 'location':
        expression = f'{location_table.name}.{column}'
    else:
        expression = 'NULL'
    return f'{expression} AS "{output_name}"'


def load_view_rows(engine, result_table, location_table, columns, ownership, unified, source):
    selected_columns = ', '.join(
        select_expression(
            column,
            result_table,
            location_table,
            ownership,
            unified,
            source,
        )
        for column in columns if ownership[column][source]
    )
    join = ''
    order = ''
    if unified:
        join = (
            f' FROM {result_table.name} '
            f'FULL JOIN {location_table.name} '
            f'ON {result_table.name}.Location_Name = '
            f'{location_table.name}.Location_Name'
        )
    elif result_table is not None:
        result_table_name = result_table.name
        selected_columns = ', '.join(
            select_expression(
                column,
                result_table,
                location_table,
                ownership,
                False,
                source,
            )
            for column in columns if ownership[column][source]
        )
        join = f' FROM {result_table_name}'
        order = (
            " ORDER BY CASE WHEN INSTR(Location_Name,'-')>0 "
            "THEN CAST(SUBSTR(Location_Name, INSTR(Location_Name,'-')+1) "
            'AS INTEGER) END, Location_Name, id'
        )
    else:
        join = f' FROM {location_table.name}'
        order = (
            " ORDER BY CASE WHEN INSTR(Location_Name,'-')>0 "
            "THEN CAST(SUBSTR(Location_Name, INSTR(Location_Name,'-')+1) "
            'AS INTEGER) END, Location_Name'
        )

    stmt = pd.read_sql(
        f'SELECT {selected_columns}{join}{order}',
        con=engine,
    )
    return stmt.to_numpy(dtype=object).tolist()


def db2df(path, selected_columns=None, mode=None):
    if path == None or path == '':
        raise Exception('No Database Chosen')

    engine = create_engine(f'sqlite:///{path}')
    metadata = MetaData()
    metadata.create_all(engine)
    tables = {
        'gw_results': Table('gw_results', metadata, autoload_with=engine),
        'gw_locations': Table('gw_locations', metadata, autoload_with=engine),
        'soil_results': Table('soil_results', metadata, autoload_with=engine),
        'soil_locations': Table('soil_locations', metadata, autoload_with=engine),
        'porewater_results': Table('porewater_results', metadata, autoload_with=engine),
        'porewater_locations': Table('porewater_locations', metadata, autoload_with=engine),
        'other_results': Table('other_results', metadata, autoload_with=engine),
        'other_locations': Table('other_locations', metadata, autoload_with=engine),
    }
    inspect(engine)

    available_columns = set()
    for table in tables.values():
        available_columns.update(table.c.keys())
    if selected_columns is None or mode is None:
        columns, mode = col_choose(list(available_columns))
    else:
        columns = selected_columns

    pairs = {
        '-GWDATA-': ('gw_results', 'gw_locations'),
        '-GWLOC-': ('gw_results', 'gw_locations'),
        '-SOILDATA-': ('soil_results', 'soil_locations'),
        '-SOILLOC-': ('soil_results', 'soil_locations'),
        '-POREDATA-': ('porewater_results', 'porewater_locations'),
        '-PORELOC-': ('porewater_results', 'porewater_locations'),
        '-OTHERDATA-': ('other_results', 'other_locations'),
        '-OTHERLOC-': ('other_results', 'other_locations'),
    }
    headers = {}
    values = {}

    for key, (result_name, location_name) in pairs.items():
        result_table = tables[result_name]
        location_table = tables[location_name]
        ownership = column_ownership(columns, result_table, location_table)
        is_result_view = key.endswith('DATA-')
        if is_result_view:
            headers[key] = [display_name(column) for column in columns if ownership[column]['result']]
        else:
            headers[key] = [display_name(column) for column in columns if ownership[column]['location']]

        if mode == 'Unified':
            values[key] = load_view_rows(
                engine,
                result_table,
                location_table,
                columns,
                ownership,
                unified=True,
                source='result',
            ) if is_result_view else []
        else:
            values[key] = load_view_rows(
                engine,
                result_table if is_result_view else None,
                location_table if not is_result_view else None,
                columns,
                ownership,
                unified=False,
                source='result' if is_result_view else 'location',
            )

    return (
        values['-GWDATA-'], values['-GWLOC-'],
        values['-SOILDATA-'], values['-SOILLOC-'],
        values['-POREDATA-'], values['-PORELOC-'],
        values['-OTHERDATA-'], values['-OTHERLOC-'], headers, columns, mode,
    )
