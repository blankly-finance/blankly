from typing import Any
from Blankly.indicators.utils import convert_to_numpy
import tulipy as ti
import pandas as pd
import numpy as np

def stdev_period(data, period=14, use_series=False) -> Any:
    if type(data) == pd.Series:
        use_series = True
    data = convert_to_numpy(data)    
    stddev = ti.stddev(data, period)
    return pd.Series(stddev) if use_series else stddev

def var_period(data, period=14) -> Any:
    if type(data) == pd.Series:
        use_series = True
    data = convert_to_numpy(data)
    var = ti.var(data, period)
    return pd.Series(var) if use_series else var

def stderr_period(data, period=14) -> Any:
    if type(data) == pd.Series:
        use_series = True
    data = convert_to_numpy(data)
    stderr = ti.stderr(data, period)
    return pd.Series(stderr) if use_series else stderr

def min_period(data, period) -> Any:
    if type(data) == pd.Series:
        use_series = True
    data = convert_to_numpy(data)
    minimum = ti.min(data, period)
    return pd.Series(minimum) if use_series else minimum

def max_period(data, period) -> Any:
    if type(data) == pd.Series:
        use_series = True
    data = convert_to_numpy(data)
    maximum = ti.max(data, period)
    return pd.Series(maximum) if use_series else maximum