from pathlib import Path
import pandas as pd
import PySimpleGUI as sg
import os
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
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
    file_split = db_default_save.split('\\')
    x = 0
    for dir in file_split:
        if '__LabReader' in dir and x != len(file_split)-1:   
            file_split = file_split[:x+1]
            break
        x += 1
    db_default_save = '\\'.join(file_split)
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
        Column('SRPID', String),
        Column('Consultant', String),
        Column('Location_Name', String, primary_key=True),
        Column('X_Coordinate', Float),
        Column('Y_Coordinate', Float),
        Column('Matrix', String),
        Column('Address', String),
        Column('AOC', String),
        Column('Date_to_Lab', Date),
        Column('Sample_Method', String),
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
        Column('SRPID', String),
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('Location_Name', String, ForeignKey('gw_locations.Location_Name'), nullable=False),
        Column('Lab_ID', String),
        Column('Analysis_Date', DateTime),
        Column('Lab_Name', String),
        Column('Analyte', String, nullable=False),
        Column('CASN', String),
        Column('Filt_Unfilt', String),
        Column('Sample_Date', Date),
        Column('Sample_Time', Time),
        Column('Result', Float),
        Column('Result_Unit', String),
        Column('Method_Detection_Limit', Float),
        Column('Analysis_Method', String),
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
        Column('SRPID', String),
        Column('Consultant', String),
        Column('Location_Name', String, primary_key=True),
        Column('X_Coordinate', Float),
        Column('Y_Coordinate', Float),
        Column('Matrix', String),
        Column('Address', String),
        Column('AOC', String),
        Column('Date_To_Lab', Date),
        Column('Sample_Method', String),
        Column('Thickness', Float),
        Column('Units_of_Thickness', String),
        Column('Bulk_Density', Float),
        Column('Units_of_Bulk_Density', String),
        Column('Percent_Low_K', Float, CheckConstraint('Percent_Low_K > 0 AND Percent_Low_K < 100')),
    )

    soil_data = Table(
        'soil_results',
        metadata_obj,
        Column('SRPID', String),
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('Location_Name', String, ForeignKey('soil_locations.Location_Name'), nullable=False),
        Column('Lab_ID', String),
        Column('Analysis_Date', DateTime),
        Column('Lab_Name', String),
        Column('Analyte', String, nullable=False),
        Column('CASN', String),
        Column('Filt_Unfilt', String),
        Column('Sample_Date', Date),
        Column('Sample_Time', Time),
        Column('Result', Float),
        Column('Result_Unit', String),
        Column('Method_Detection_Limit', Float),
        Column('Analysis_Method', String),
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
        Column('SRPID', String),
        Column('Consultant', String),
        Column('Location_Name', String, primary_key=True),
        Column('X_Coordinate', Float),
        Column('Y_Coordinate', Float),
        Column('Matrix', String),
        Column('Address', String),
        Column('AOC', String),
        Column('Date_To_Lab', Date),
        Column('Sample_Method', String)
    )

    porewater_data = Table(
        'porewater_results',
        metadata_obj,
        Column('SRPID', String),
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('Location_Name', String, ForeignKey('porewater_locations.Location_Name'), nullable=False),
        Column('Lab_ID', String),
        Column('Analysis_Date', DateTime),
        Column('Lab Name', String),
        Column('Analyte', String, nullable=False),
        Column('CASN', String),
        Column('Filt_Unfilt', String),
        Column('Sample_Date', Date),
        Column('Sample_Time', Time),
        Column('Result', Float),
        Column('Result_Unit', String),
        Column('Method_Detection_Limit', Float),
        Column('Analysis_Method', String),
        Column('Flag', String),
        Column('Detect', Boolean),
        Column('Trace', Boolean),
        Column('Duplicate', Boolean),
        Column('Exclude', Boolean),
        Column('Chem_Group', String),
    )

    other_location = Table(
        'other_locations',
        metadata_obj,
        Column('SRPID', String),
        Column('Consul', String),
        Column('Location_Name', String, primary_key=True),
        Column('X_Coordinate', Float),
        Column('Y_Coordinate', Float),
        Column('Matrix', String),
        Column('Address', String),
        Column('AOC', String),
        Column('Date_to_Lab', Date),
        Column('Sample_Method', String)
    )

    other_data = Table(
        'other_results',
        metadata_obj,
        Column('SRPID', String),
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('Location_Name', String, ForeignKey('porewater_locations.Location_Name'), nullable=False),
        Column('Lab_ID', String),
        Column('Analysis_Date', DateTime),
        Column('Lab_Name', String),
        Column('Analyte', String, nullable=False),
        Column('CASN', String),
        Column('Filt_Unfilt', String),
        Column('Sample_Date', Date),
        Column('Sample_Time', Time),
        Column('Result', Float),
        Column('Result_Unit', String),
        Column('Method_Detection_Limit', Float),
        Column('Analysis_Method', String),
        Column('Flag', String),
        Column('Detect', Boolean),
        Column('Trace', Boolean),
        Column('Duplicate', Boolean),
        Column('Exclude', Boolean),
        Column('Chem_Group', String),
    )

    metadata_obj.create_all(engine)
    return db_path