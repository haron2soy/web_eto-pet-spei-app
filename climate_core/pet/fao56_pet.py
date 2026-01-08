from climate_core.eto.fao56 import FAO56ETo

def pet_from_eto(df):
    if "ETo" not in df.columns:
        FAO56ETo(df).compute()
    return df["ETo"]
