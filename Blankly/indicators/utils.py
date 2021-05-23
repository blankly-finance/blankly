import pandas as pd
import tulipy as ti
import numpy as np

def to_historical_returns(data):
    return pd.series(data).diff().tolist()