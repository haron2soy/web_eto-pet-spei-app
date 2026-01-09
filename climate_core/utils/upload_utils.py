import pandas as pd
COLUMN_MAPPINGS = {
    'StationID': ['stationid', 'station_id', 'id', 'Station_ID', 'station_Id'],
    'Station_Name': ['stationname', 'station_name', 'name', 'station_Name'],
    'Year': ['year', 'yy', 'yr'],
    'Month': ['month', 'mm'],
    'Tmax': ['tmax', 'tmpmax', 'tasmax', 'tx', 'maxtemp', ],
    'Tmin': ['tmin', 'tmpmin', 'tasmin', 'tn', 'mintemp'],
    'Tmean': ['tmean', 'tmp', 'tas', 'tm', 'meantemp'],
    'Precip': ['precip', 'prcp', 'p', 'rain'],
    'RH': ['rh', 'relativehumidity'],
    'PS': ['pressure', 'SurfacePressure', 'pres', 'Press','ps'],
    'RHmax': ['rhmax', 'rh_max'],
    'RHmin': ['rhmin', 'rh_min'],
    'Rs': ['rs', 'solarradiation', 'rad'],
    'WD': ['wd', 'wnddir'],
    'WS':['ws', 'wndspd', 'windspeed'],
    'Lat': ['lat', 'latitude'],
    'Lon': ['lon', 'longitude'],
    'Elev': ['elev', 'elevation', 'alt'],
}
NORMALIZED_MAPPINGS = {
    canonical.lower(): [a.lower() for a in aliases]
    for canonical, aliases in COLUMN_MAPPINGS.items()
}

# -------------------------------------------------------------------
# 3. Canonical column set (THIS IS WHERE YOU ADD IT)
# -------------------------------------------------------------------
CANONICAL_COLUMNS = {k.lower() for k in COLUMN_MAPPINGS.keys()}

# explicitly include time + station identifiers
CANONICAL_COLUMNS |= {
    "stationid",
    "station_name",
    "year",
    "month",    
}

def detect_duplicate_variables(dfs, canonical_columns):
    """
    Detects canonical variable columns that appear in multiple files.
    Returns:
        duplicates: dict[var_name] = list of file indices where it appears
    """
    duplicates = {}

    for i, df in enumerate(dfs):
        vars_in_df = [c for c in df.columns if c in canonical_columns and c not in ["station_name","stationid","year","month"]]
        for var in vars_in_df:
            duplicates.setdefault(var, []).append(i)

    # keep only variables that appear in more than one file
    duplicates = {k:v for k,v in duplicates.items() if len(v) > 1}

    return duplicates

def apply_column_mappings(df: pd.DataFrame):
    rename_map = {}
    undetected_cols = []

    # alias → canonical
    for col in df.columns:
        mapped = False
        for canonical, aliases in NORMALIZED_MAPPINGS.items():
            if col in aliases:
                rename_map[col] = canonical
                mapped = True
                break

        if not mapped and col not in CANONICAL_COLUMNS:
            rename_map[col] = f"{col}_undetected"
            undetected_cols.append(f"{col}_undetected")

    df = df.rename(columns=rename_map)
    df.attrs["undetected_columns"] = undetected_cols

    return df

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip().lower() for c in df.columns]
    return df

def validate_minimum_schema(df: pd.DataFrame):
    cols = set(df.columns)

    if not {"station_name", "stationid"}.intersection(cols):
        raise ValueError("Missing station identifier")

    if not {"year", "month"}.issubset(cols):
        raise ValueError("Year and Month columns are required")

    climate_vars = cols & CANONICAL_COLUMNS - {
        "station_name", "stationid", "year", "month"
    }

    if not climate_vars:
        raise ValueError("No usable climate variables detected")

    return True

def get_preview_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    preview_cols = [
        c for c in df.columns if c in CANONICAL_COLUMNS
    ]
    return df[preview_cols]

def extract_stationid_map(dfs):
    station_map = {}

    for df in dfs:
        if "stationid" not in df.columns:
            continue

        for _, row in df[["station_name", "stationid"]].dropna().iterrows():
            st = row["station_name"]
            sid = row["stationid"]

            if st in station_map and station_map[st] != sid:
                raise ValueError(
                    f"Inconsistent stationid for station '{st}'"
                )

            station_map[st] = sid

    return station_map
def merge_climate_dataframes(dfs):
    merged_df = None
    key_cols = ["station_name", "year", "month"]

    for df in dfs:
        df = df.drop(columns=["stationid"], errors="ignore")

        keep_cols = key_cols + [
            c for c in df.columns
            if c in CANONICAL_COLUMNS and c not in key_cols
        ]

        df = df[keep_cols]

        if merged_df is None:
            merged_df = df
        else:
            merged_df = pd.merge(
                merged_df,
                df,
                on=key_cols,
                how="outer"
            )

    return merged_df

def attach_stationid(df, station_map):
    df["stationid"] = df["station_name"].map(station_map)
    return df


    '''def validate_minimum_schema(df: pd.DataFrame):
    cols = set(df.columns)

    if not any(c in cols for c in STATION_COLS):
        raise ValueError("Missing station name column")

    if not all(c in cols for c in REQUIRED_TIME_COLS):
        raise ValueError("Year and Month columns are required")

    climate_vars = cols - set(REQUIRED_TIME_COLS) - set(STATION_COLS) - {"stationid"}
    if len(climate_vars) == 0:
        raise ValueError("At least one climate variable is required")

    return True'''
