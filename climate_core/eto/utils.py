import numpy as np

def tmean(df):
    if "Tmean" not in df.columns:
        df["Tmean"] = (df["Tmax"] + df["Tmin"]) / 2

def saturation_vapor_pressure(T):
    return 0.6108 * np.exp((17.27 * T) / (T + 237.3))

def slope_vapor_pressure_curve(Tmean):
    es = saturation_vapor_pressure(Tmean)
    return 4098 * es / (Tmean + 237.3) ** 2
