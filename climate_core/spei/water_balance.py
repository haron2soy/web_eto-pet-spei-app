class WaterBalance:
    """
    Owner of: D
    """

    def __init__(self, df):
        self.df = df

    def compute(self):
        if "D" in self.df.columns:
            return self.df["D"]

        if "PET" not in self.df.columns:
            raise ValueError("PET must be computed before water balance")

        self.df["D"] = self.df["P"] - self.df["PET"]
        return self.df["D"]
