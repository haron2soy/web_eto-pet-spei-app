class PETCalculator:
    """
    Owner of: PET
    """

    def __init__(self, method="fao56"):
        self.method = method

    def compute(self, df):
        if "PET" in df.columns:
            return df["PET"]

        if self.method == "fao56":
            from .fao56_pet import pet_from_eto
            df["PET"] = pet_from_eto(df)

        elif self.method == "thornthwaite":
            from .thornthwaite import thornthwaite_pet
            df["PET"] = thornthwaite_pet(df)

        elif self.method == "hargreaves":
            from .hargreaves import hargreaves_pet
            df["PET"] = hargreaves_pet(df)

        else:
            raise ValueError(f"Unknown PET method: {self.method}")

        return df["PET"]
