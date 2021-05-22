import pandas as pd

def to_historical_returns(data):
    return pd.series(data).diff().tolist()