import os
import pandas as pd
from climate_core.eto.fao56 import FAO56ETo
from climate_core.pet.base import PETCalculator
from climate_core.spei.water_balance import WaterBalance
from climate_core.spei.standardization import SPEICalculator


class PipelineManager:
    """
    Job-scoped climate computation pipeline.
    """

    def __init__(self, job_id, workdir, pet_method="fao56"):
        self.job_id = job_id
        self.workdir = workdir
        self.pet_method = pet_method
        self.df = None

    # ---------- IO ----------
    def load_input(self, filepath):
        self.df = pd.read_csv(filepath, parse_dates=["date"])
        self.df.sort_values(["StationID", "date"], inplace=True)

    def cache_path(self, name):
        return os.path.join(self.workdir, f"{self.job_id}_{name}.parquet")

    def load_cache(self, name):
        path = self.cache_path(name)
        if os.path.exists(path):
            return pd.read_parquet(path)
        return None

    def save_cache(self, name):
        self.df.to_parquet(self.cache_path(name), index=False)

    # ---------- PIPELINE ----------
    def compute_eto(self):
        if "ETo" not in self.df.columns:
            FAO56ETo(self.df).compute()

    def compute_pet(self):
        if "PET" not in self.df.columns:
            PETCalculator(self.pet_method).compute(self.df)

    def compute_water_balance(self):
        if "D" not in self.df.columns:
            WaterBalance(self.df).compute()

    def compute_spei(self, scales=(3, 6, 12)):
        spei = SPEICalculator(self.df)
        for k in scales:
            spei.compute(k=k)

    def run(self, scales=(3, 6, 12)):
        self.compute_eto()
        self.compute_pet()
        self.compute_water_balance()
        self.compute_spei(scales=scales)

        return self.df
