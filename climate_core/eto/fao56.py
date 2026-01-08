import numpy as np
from .utils import tmean, saturation_vapor_pressure, slope_vapor_pressure_curve
from climate_core.common.constants import CP, LAMBDA, EPSILON
from climate_core.common.validation import require_columns

class FAO56ETo:
    """
    Owner of: ETo
    """

    def __init__(self, df):
        self.df = df

    def compute(self):
        if "ETo" in self.df.columns:
            return self.df["ETo"]

        require_columns(self.df, ["Tmax", "Tmin", "RH", "Rs", "u2", "P"])

        tmean(self.df)

        es = (saturation_vapor_pressure(self.df["Tmax"]) +
              saturation_vapor_pressure(self.df["Tmin"])) / 2

        ea = es * self.df["RH"] / 100
        delta = slope_vapor_pressure_curve(self.df["Tmean"])
        gamma = 0.665e-3 * self.df.get("PS", 101.3)

        Rn = self.df["Rs"] * 0.77  # simplified net radiation

        eto = (
            (0.408 * delta * Rn +
             gamma * (900 / (self.df["Tmean"] + 273)) *
             self.df["u2"] * (es - ea))
            /
            (delta + gamma * (1 + 0.34 * self.df["u2"]))
        )

        self.df["ETo"] = eto.clip(lower=0)
        return self.df["ETo"]
