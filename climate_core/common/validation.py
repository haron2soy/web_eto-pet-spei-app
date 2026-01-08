REQUIRED_COLUMNS = {
    "fao56": ["Tmax", "Tmin", "RH", "Rs", "u2", "P", "date"]
}

def require_columns(df, cols):
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
