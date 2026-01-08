import numpy as np
from scipy.stats import fisk
from .aggregation import aggregate

class SPEICalculator:
    """
    Owner of: SPEI
    """

    def __init__(self, df):
        self.df = df

    def compute(self, k=3):
        col = f"SPEI_{k}"

        if col in self.df.columns:
            return self.df[col]

        if "D" not in self.df.columns:
            raise ValueError("Water balance D must exist")

        Dk = aggregate(self.df["D"], k)
        valid = Dk.dropna()

        params = fisk.fit(valid)
        cdf = fisk.cdf(Dk, *params)

        self.df[col] = np.clip(
            np.sqrt(2) * np.erfinv(2 * cdf - 1),
            -3, 3
        )

        return self.df[col]
