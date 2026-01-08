import pandas as pd

from climate_core.eto.fao56 import FAO56ETo
from climate_core.pet.base import PETCalculator
from climate_core.spei.water_balance import WaterBalance
from climate_core.spei.standardization import SPEICalculator


def compute_climate(df, spei_scales=(3, 6, 12), pet_method="fao56"):
    """
    Compute ETo, PET, Water Balance, and SPEI.
    Safe against recomputation.
    """

    if "ETo" not in df.columns:
        FAO56ETo(df).compute()

    if "PET" not in df.columns:
        PETCalculator(method=pet_method).compute(df)

    if "D" not in df.columns:
        WaterBalance(df).compute()

    for k in spei_scales:
        spei_col = f"SPEI_{k}"
        if spei_col not in df.columns:
            SPEICalculator(df).compute(k=k)

    return df
