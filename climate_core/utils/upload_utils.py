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

'''def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip().lower() for c in df.columns]
    return df'''
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip().lower() for c in df.columns]

    if "station_name" in df.columns:
        df["station_name"] = (
            df["station_name"]
            .astype(str)
            .str.strip()
            .str.lower()
        )

    return df
def collect_missing_stationids(dfs, station_map):
    all_stations = set()

    for df in dfs:
        all_stations.update(df["station_name"].dropna().unique())

    missing = sorted(all_stations - set(station_map.keys()))
    return missing
    
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
    all_stations = set()

    for df in dfs:
        all_stations.update(df["station_name"].dropna().unique())

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

    missing_stations = sorted(all_stations - set(station_map.keys()))

    return station_map, missing_stations

'''def merge_climate_dataframes(dfs):
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

    return merged_df'''

def merge_climate_dataframes(dfs, selected_columns=None):
    """
    selected_columns: dict[var_name] = file_index
    """
    merged_df = None
    key_cols = ["station_name", "year", "month"]

    for i, df in enumerate(dfs):
        df = df.drop(columns=["stationid"], errors="ignore")

        # Keep only canonical variables, but if variable is a duplicate, keep it only if this file is selected
        keep_cols = key_cols[:]
        for col in df.columns:
            if col in key_cols:
                continue
            if col in CANONICAL_COLUMNS:
                if selected_columns and col in selected_columns:
                    if selected_columns[col] != i:
                        continue  # skip this duplicate column
                keep_cols.append(col)

        df = df[keep_cols]

        if merged_df is None:
            merged_df = df
        else:
            for col in df.columns:
                if col in key_cols:
                    continue
                if col in merged_df.columns:
                    merged_df[col] = merged_df[col].combine_first(df[col])
                else:
                    merged_df[col] = df[col]

    return merged_df


def attach_stationid(df, station_map):
    df["stationid"] = df["station_name"].map(station_map)
    return df

def resolve_duplicates_by_data_count(dfs, duplicates):
    """
    For each duplicate variable, select the file with the most non-NaN rows.
    Returns:
        selected_columns: dict[var_name] = selected file index
        conflicts_metadata: list of info for frontend
    """
    selected_columns = {}
    conflicts_metadata = []

    for var, file_indices in duplicates.items():
        counts = [(i, dfs[i][var].notna().sum()) for i in file_indices]
        counts.sort(key=lambda x: x[1], reverse=True)  # more non-NaN first

        best_file_index = counts[0][0]
        selected_columns[var] = best_file_index

        # store metadata for frontend
        conflict_info = {
            "variable": var,
            "files": file_indices,
            "counts": {i: dfs[i][var].notna().sum() for i in file_indices},
            "selected": best_file_index
        }
        conflicts_metadata.append(conflict_info)

    return selected_columns, conflicts_metadata
