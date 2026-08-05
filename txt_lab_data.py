import os
import argparse
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from datetime import datetime

# Columns in your sample header (will be normalized)
EXPECTED_COLS = [
    "SRPID","Sampdate","Sampnum","Labid","Tdanalyze","Labname","Njdlabcert","Resulttype",
    "Analtparam","Cas","Filtunfilt","Conc","Concunits","Qaqual","Mdl","Quanttype","Quantlevel",
    "Anlys_mthd","QAQC","Uncor_conc","Uncor_unit","Reten_time","Dilut_fac","Prep_mthd","Clnup_mthd"
]

def find_txt_files(folder):
    for root, _, files in os.walk(folder):
        for f in files:
            if f.lower().endswith('.txt'):
                yield os.path.join(root, f)

def read_hzresult(path, encoding='utf-8'):
    # read as TSV, let pandas create extra columns if present
    df = pd.read_csv(path, sep='\t', engine='python', encoding=encoding, dtype=str)
    # strip whitespace-only column names & values
    df.columns = [c.strip() if isinstance(c, str) else c for c in df.columns]
    df = df.applymap(lambda v: v.strip() if isinstance(v, str) else v)
    return df

def normalize_columns(df):
    # standardize header names: lower, strip, replace spaces with underscore
    new_cols = []
    for c in df.columns:
        if not isinstance(c, str):
            new_cols.append(str(c))
            continue
        nc = c.strip().lower().replace(' ', '_').replace('/', '_').replace('-', '_')
        new_cols.append(nc)
    df.columns = new_cols
    return df

def clean_and_cast(df):
    # Common replacements: 'ND' or 'ND ' -> NaN; blank strings -> NaN; numeric strings like '10.' -> '10'
    df = df.replace({'ND': np.nan, '': np.nan, 'N/A': np.nan, 'NA': np.nan})
    # trim trailing '.' in numeric-looking tokens: '10.' -> '10'
    def tidy_numeric_text(x):
        if isinstance(x, str):
            s = x.strip()
            # avoid touching chemical names like '1,1-DICHLOROETHANE'
            # Only modify if string looks like a number (digits, optional decimal, optional leading +/-)
            if s.replace('.', '', 1).replace('-', '', 1).isdigit():
                # remove trailing dot or leading/trailing punctuation
                return s.rstrip('.')
        return x

    df = df.applymap(tidy_numeric_text)

    # parse dates
    # Sampdate appears like 12/17/2012 -> parse to date
    if 'sampdate' in df.columns:
        df['sampdate_parsed'] = pd.to_datetime(df['sampdate'], errors='coerce', dayfirst=False, infer_datetime_format=True)
    # Tdanalyze appears like 12/18/2012 10:23 -> parse to datetime
    if 'tdanalyze' in df.columns:
        df['tdanalyze_parsed'] = pd.to_datetime(df['tdanalyze'], errors='coerce', dayfirst=False, infer_datetime_format=True)

    # numeric columns to coerce
    numeric_candidates = ['conc','uncor_conc','reten_time','dilut_fac','quantlevel']
    for col in numeric_candidates:
        if col in df.columns:
            df[col+'_num'] = pd.to_numeric(df[col], errors='coerce')

    # Preserve original textual result indicator (like 'ND', '1.6', 'J') in 'conc' column; numeric in conc_num
    # If you want a single canonical numeric value (e.g., interpret 'ND' as 0), handle after import.

    return df

def main(input_dir, db_path, table_name, if_exists='append'):
    engine = create_engine(f"sqlite:///{db_path}")

    first = True
    total = 0
    for path in find_txt_files(input_dir):
        print("Reading", path)
        df = read_hzresult(path)
        if df is None or df.shape[0] == 0:
            print("  skipped (empty)")
            continue

        df = normalize_columns(df)
        df = clean_and_cast(df)

        # Add source filename for provenance
        df['source_file'] = os.path.basename(path)

        # Write to SQL (append). Let pandas infer SQL types.
        df.to_sql(table_name, engine, if_exists='append' if not first else if_exists, index=False, chunksize=1000, method='multi')
        first = False
        print(f"  inserted {len(df)} rows into {table_name}")
        total += len(df)

    print("Done. Total rows:", total)
    print("You can query the SQLite DB with sqlite3 or a GUI. Example:")
    print(f"  sqlite3 {db_path} \"SELECT sampdate_parsed, sampnum, analtparam, conc, conc_num FROM {table_name} LIMIT 10;\"")

if __name__ == '__main__':
    p = argparse.ArgumentParser(description="Import hzresult-style TSV .txt files into SQLite")
    p.add_argument('input_dir', help='Directory with .txt files (or file path)')
    p.add_argument('--db', default='hzresults.db', help='SQLite DB file (default: hzresults.db)')
    p.add_argument('--table', default='hzresults', help='Target DB table name')
    p.add_argument('--if-exists', default='append', choices=['append','replace','fail'], help='SQLite to_sql if_exists policy')
    args = p.parse_args()
    main(args.input_dir, args.db, args.table, if_exists=args.if_exists)