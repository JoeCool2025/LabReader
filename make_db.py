from pathlib import Path
import pandas as pd
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
    create_engine,
)

def db_maker(file):
    df = pd.read_csv(file, sep='\t')

    db_name = df.iloc[0, 0] + '.db'
    db_dir = Path(__file__).resolve().parent / 'Databases'
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = db_dir / db_name
    engine = create_engine(f'sqlite:///{db_path}')
    metadata_obj = MetaData()

    gw_location_table = Table(
        'gw_locations',
        metadata_obj,
        Column('Location_Name', String, primary_key=True),
        Column('X Coordinate', Float),
        Column('Y Coordinate', Float),
        Column('Longitude', Float),
        Column('Latitude', Float),
        Column('Layer', String),
        Column('Source_Tail', String, CheckConstraint("Source_Tail IN ('S', 'T') OR Source_Tail IS NULL")),
        Column('Saturated Thickness', Float),
        Column('Units of ST', String),
        Column('Porosity', Float),
    )

    gw_data = Table(
        'gw_results',
        metadata_obj,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('Location Name', String, ForeignKey('gw_locations.Location_Name'), nullable=False),
        Column('Analyte', String, nullable=False),
        Column('Sample Date', Date, nullable=False),
        Column('Result', Float),
        Column('Result Unit', String, nullable=False),
        Column('Method Detection Limit', Float),
        Column('Flag', String),
        Column('Detect', Boolean),
        Column('Trace', Boolean),
        Column('Duplicate', Boolean),
        Column('Exclude', Boolean),
        Column('Chem Group', String),
    )

    soil_location = Table(
        'soil_locations',
        metadata_obj,
        Column('Location_Name', String, primary_key=True),
        Column('X Coordinate', Float),
        Column('Y Coordinate', Float),
        Column('Longitude', Float),
        Column('Latitude', Float),
        Column('Thickness', Float),
        Column('Units of Thickness', String),
        Column('Bulk Density', Float),
        Column('Units of Bulk Density', String),
        Column('Percent_Low_K', Float, CheckConstraint('Percent_Low_K > 0 AND Percent_Low_K < 100')),
    )

    soil_data = Table(
        'soil_results',
        metadata_obj,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('Location Name', String, ForeignKey('soil_locations.Location_Name'), nullable=False),
        Column('Analyte', String, nullable=False),
        Column('Sample Date', Date, nullable=False),
        Column('Result', Float),
        Column('Result Unit', String, nullable=False),
        Column('Method Detection Limit', Float),
        Column('Flag', String),
        Column('Detect', Boolean),
        Column('Trace', Boolean),
        Column('Duplicate', Boolean),
        Column('Exclude', Boolean),
        Column('Chem Group', String),
    )

    porewater_location = Table(
        'porewater_locations',
        metadata_obj,
        Column('Location_Name', String, primary_key=True),
        Column('X Coordinate', Float),
        Column('Y Coordinate', Float),
        Column('Longitude', Float),
        Column('Latitude', Float),
    )

    porewater_data = Table(
        'porewater_results',
        metadata_obj,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('Location Name', String, ForeignKey('porewater_locations.Location_Name'), nullable=False),
        Column('Analyte', String, nullable=False),
        Column('Sample Date', Date, nullable=False),
        Column('Result', Float),
        Column('Result Unit', String, nullable=False),
        Column('Method Detection Limit', Float),
        Column('Flag', String),
        Column('Detect', Boolean),
        Column('Trace', Boolean),
        Column('Duplicate', Boolean),
        Column('Exclude', Boolean),
        Column('Chem Group', String),
    )

    metadata_obj.create_all(engine)
    return db_path