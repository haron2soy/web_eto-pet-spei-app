def aggregate(series, k):
    return series.rolling(k, min_periods=k).sum()
