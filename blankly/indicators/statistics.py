from typing import Any
from blankly.indicators.utils import convert_to_numpy
from blankly.indicators.utils import check_series
import tulipy as ti
import pandas as pd


def stddev_period(data, period=14, use_series=False) -> Any:
    if check_series(data):
        use_series = True
    data = convert_to_numpy(data)    
    stddev = ti.stddev(data, period)
    return pd.Series(stddev) if use_series else stddev


def var_period(data, period=14, use_series=False) -> Any:
    if check_series(data):
        use_series = True
    data = convert_to_numpy(data)
    var = ti.var(data, period)
    return pd.Series(var) if use_series else var


def stderr_period(data, period=14, use_series=False) -> Any:
    if check_series(data):
        use_series = True
    data = convert_to_numpy(data)
    stderr = ti.stderr(data, period)
    return pd.Series(stderr) if use_series else stderr


def min_period(data, period, use_series=False) -> Any:
    if check_series(data):
        use_series = True
    data = convert_to_numpy(data)
    minimum = ti.min(data, period)
    return pd.Series(minimum) if use_series else minimum


def max_period(data, period, use_series=False) -> Any:
    if check_series(data):
        use_series = True
    data = convert_to_numpy(data)
    maximum = ti.max(data, period)
    return pd.Series(maximum) if use_series else maximum


def sum_period(data, period, use_series=False) -> Any:
    if check_series(data):
        use_series = True
    data = convert_to_numpy(data)
    maximum = ti.sum(data, period)
    return pd.Series(maximum) if use_series else maximum
