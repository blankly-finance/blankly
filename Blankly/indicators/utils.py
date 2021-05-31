from typing import Any
import pandas as pd
import numpy as np


def to_historical_returns(data: Any):
    return pd.Series(data).diff().tolist()


def convert_to_numpy(data: Any): 
    if type(data) == list:
        return np.asarray(data)
    elif type(data) == pd.Series:
        return data.to_numpy()
    return data


def check_series(data: Any):
    return isinstance(data, pd.Series)
