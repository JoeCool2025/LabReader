import pandas as pd
import sqlalchemy as sqla

input_file = input("Enter the path to the input TSV file: ")
df = pd.read_csv(input_file, sep='\t')
print(df)

engine = sqla.create_engine('sqlite:///:memory:')
metadata_obj = sqla.MetaData()

ubw_colonade_gw_data = sqla.Table(
    'ubw_colonade_gw_results',
    metadata_obj,
    sqla.Column('id', sqla.Integer, primary_key=True, autoincrement=True),
    sqla.Column('Location Name', sqla.String, sqla.ForeignKey('ubw_colonade_gw_locations.Location_Name'), nullable = False),
    sqla.Column('Analyte', sqla.String, nullable = False),
    sqla.Column('Sample Date', sqla.Date, nullable = False),
    sqla.Column('Result', sqla.Float, nullable = False),
    sqla.Column('Result Unit', sqla.String, nullable = False),
    sqla.Column('Method Detection Limit', sqla.Float, nullable = False),
    sqla.Column('Flag', sqla.String),
    sqla.Column('Detect', sqla.Boolean, nullable = False),
    sqla.Column('Trace', sqla.Boolean, nullable = False),
    sqla.Column('Duplicate', sqla.Boolean, nullable = False),
    sqla.Column('Exclude', sqla.Boolean, nullable = False),
    sqla.Column('Chem Group', sqla.String)
)

ubw_colonade_gw_locations_table = sqla.Table(
    'ubw_colonade_gw_locations',
    metadata_obj,
    sqla.Column('Location_Name', sqla.String, primary_key=True),
    sqla.Column('X Coordinate', sqla.Float),
    sqla.Column('Y Coordinate', sqla.Float),
    sqla.Column('Longitude', sqla.Float),
    sqla.Column('Latitude', sqla.Float),
    sqla.Column('Layer', sqla.String),
    sqla.Column('Source_Tail', sqla.String, sqla.CheckConstraint("Source_Tail IN ('S', 'T') OR Source_Tail IS NULL")),
    sqla.Column('Saturated Thickness', sqla.Float),
    sqla.Column('Units of ST', sqla.String),
    sqla.Column('Porosity', sqla.Float)
)
metadata_obj.create_all(engine)

with engine.connect() as conn:
    for row in df.loc[:, 'Sampnum'].unique():
        result = conn.execute(
            sqla.insert(ubw_colonade_gw_locations_table),
            [{"Location_Name": row}]
        )
        conn.commit()

stmt = sqla.select(ubw_colonade_gw_locations_table)
with engine.connect() as conn:
    for row in conn.execute(stmt):
        print(row)