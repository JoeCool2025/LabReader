from pathlib import Path
import pandas as pd
import PySimpleGUI as sg
import os
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Time,
    create_engine,
)

def db_maker(file):
    df = pd.read_csv(file, sep='\t')
    db_default_save = os.path.dirname(os.path.abspath(__file__))
    db_default_save += '\\Databases'

    db_name = df.iloc[0, 0] + '.db'
    db_dir = sg.popup_get_folder('Select Database Save Folder', initial_folder=db_default_save)
    db_dir = Path(db_dir)
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = db_dir / db_name
    engine = create_engine(f'sqlite:///{db_path}')
    metadata_obj = MetaData()

    gw_location_table = Table(
        'gw_locations',
        metadata_obj,
        Column('Location_Name', String, primary_key=True),
        Column('X_Coordinate', Float),
        Column('Y_Coordinate', Float),
        Column('Longitude', String),
        Column('Latitude', String),
        Column('Matrix', String),
        Column('Address', String),
        Column('AOC', String),
        Column('Layer', String),
        Column('Depth_To_Top_Of_Well', String),
        Column('Depth_To_Bottom_Of_Well', String),
        Column('Depth_To_Top_Of_Screen', String),
        Column('Depth_To_Bottom_Of_Screen', String),
        Column('Ground_Elevation', String),
        Column('Well_Elevation', String),
        Column('Source_Tail', String, CheckConstraint("Source_Tail IN ('S', 'T') OR Source_Tail IS NULL")),
        Column('Saturated_Thickness', Float),
        Column('Units_of_ST', String),
        Column('Porosity', Float),
    )

    gw_data = Table(
        'gw_results',
        metadata_obj,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('Location_Name', String, ForeignKey('gw_locations.Location_Name'), nullable=False),
        Column('Analyte', String, nullable=False),
        Column('CASN', String),
        Column('Sample_Date', Date, nullable=False),
        Column('Sample_Time', Time),
        Column('Result', Float),
        Column('Result_Unit', String, nullable=False),
        Column('Method_Detection_Limit', Float),
        Column('Flag', String),
        Column('Detect', Boolean),
        Column('Trace', Boolean),
        Column('Duplicate', Boolean),
        Column('Exclude', Boolean),
        Column('Chem_Group', String),
    )

    soil_location = Table(
        'soil_locations',
        metadata_obj,
        Column('Location_Name', String, primary_key=True),
        Column('X_Coordinate', Float),
        Column('Y_Coordinate', Float),
        Column('Longitude', String),
        Column('Latitude', String),
        Column('Matrix', String),
        Column('Address', String),
        Column('AOC', String),
        Column('Thickness', Float),
        Column('Units_of_Thickness', String),
        Column('Bulk_Density', Float),
        Column('Units_of_Bulk_Density', String),
        Column('Percent_Low_K', Float, CheckConstraint('Percent_Low_K > 0 AND Percent_Low_K < 100')),
    )

    soil_data = Table(
        'soil_results',
        metadata_obj,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('Location_Name', String, ForeignKey('soil_locations.Location_Name'), nullable=False),
        Column('Analyte', String, nullable=False),
        Column('CASN', String),
        Column('Sample_Date', Date, nullable=False),
        Column('Sample_Time', Time),
        Column('Result', Float),
        Column('Result_Unit', String, nullable=False),
        Column('Method_Detection_Limit', Float),
        Column('Flag', String),
        Column('Detect', Boolean),
        Column('Trace', Boolean),
        Column('Duplicate', Boolean),
        Column('Exclude', Boolean),
        Column('Chem_Group', String),
    )

    porewater_location = Table(
        'porewater_locations',
        metadata_obj,
        Column('Location_Name', String, primary_key=True),
        Column('X_Coordinate', Float),
        Column('Y_Coordinate', Float),
        Column('Longitude', String),
        Column('Latitude', String),
        Column('Matrix', String),
        Column('Address', String),
        Column('AOC', String),
    )

    porewater_data = Table(
        'porewater_results',
        metadata_obj,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('Location_Name', String, ForeignKey('porewater_locations.Location_Name'), nullable=False),
        Column('Analyte', String, nullable=False),
        Column('CASN', String),
        Column('Sample_Date', Date, nullable=False),
        Column('Sample_Time', Time),
        Column('Result', Float),
        Column('Result_Unit', String, nullable=False),
        Column('Method_Detection_Limit', Float),
        Column('Flag', String),
        Column('Detect', Boolean),
        Column('Trace', Boolean),
        Column('Duplicate', Boolean),
        Column('Exclude', Boolean),
        Column('Chem_Group', String),
    )

    metadata_obj.create_all(engine)
    return db_path