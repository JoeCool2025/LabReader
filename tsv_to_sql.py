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
    sqla.Column('Location Name', sqla.String),
    sqla.Column('Analyte', sqla.String),
    sqla.Column('Sample Date', sqla.Date),
    sqla.Column('Result', sqla.Float),
    sqla.Column('Result Unit', sqla.String),
    sqla.Column('Method Detection Limit', sqla.Float),
    sqla.Column('Flag', sqla.String),
    sqla.Column('Detect', sqla.Boolean),
    sqla.Column('Trace', sqla.Boolean),
    sqla.Column('Duplicate', sqla.Boolean),
    sqla.Column('Exclude', sqla.Boolean),
    sqla.Column('Chem Group', sqla.String)
)

ubw_colonade_gw_locations = sqla.Table(
    'ubw_colonade_gw_locations',
    metadata_obj,
    sqla.Column('Location Name', sqla.String, primary_key=True),
    sqla.Column('X Coordinate', sqla.Float),
    sqla.Column('Y Coordinate', sqla.Float),
    sqla.Column('Longitude', sqla.Float),
    sqla.Column('Latitude', sqla.Float),
    sqla.Column('Layer', sqla.String),
    sqla.Column('Source_Tail', sqla.CheckConstraint("status IN ('S', 'T') OR status IS NULL")),
    sqla.Column('Saturated Thickness', sqla.Float),
    sqla.Column('Units of ST', sqla.String),
    sqla.Column('Porosity', sqla.Float)
)

#with engine.connect() as conn:
    #for row in df.iloc[:, 2]:
        #result = conn.execute(
            #sqla.insert(ubw_colonade_gw_locations),[{"Location Name": row}],)
        #conn.commit()

# stmt = sqla.select(ubw_colonade_gw_locations.c['Location Name'])
# with engine.connect() as conn:
    #for row in conn.execute(stmt):
        #print(row)