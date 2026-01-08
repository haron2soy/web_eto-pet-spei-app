import numpy as np

def thornthwaite_pet(df):
    if "Tmean" not in df.columns:
        df["Tmean"] = (df["Tmax"] + df["Tmin"]) / 2

    T = df["Tmean"].clip(lower=0)
    return 16 * (T / 5) ** 1.514
