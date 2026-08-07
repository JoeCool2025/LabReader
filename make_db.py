from pathlib import Path
import pandas as pd
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    Float,
    ForeignKey,
    Insert,
    Integer,
    MetaData,
    String,
    Table,
    select,
    create_engine,
    exc
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
        Column('Result', Float, nullable=False),
        Column('Result Unit', String, nullable=False),
        Column('Method Detection Limit', Float),
        Column('Flag', String),
        Column('Detect', Boolean), #nullable=False),
        Column('Trace', Boolean), #nullable=False),
        Column('Duplicate', Boolean), #nullable=False),
        Column('Exclude', Boolean), #nullable=False),
        Column('Chem Group', String),
    )

    metadata_obj.create_all(engine)
    return db_path