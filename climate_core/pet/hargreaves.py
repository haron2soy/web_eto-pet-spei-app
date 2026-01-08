import numpy as np

def hargreaves_pet(df):
    if "Tmean" not in df.columns:
        df["Tmean"] = (df["Tmax"] + df["Tmin"]) / 2

    return 0.0023 * (df["Tmean"] + 17.8) * (df["Tmax"] - df["Tmin"]) ** 0.5
