from blankly.indicators.utils import convert_to_numpy
from blankly.indicators.utils import check_series
import numpy as np
import pandas as pd
import tulipy as ti


def bbands(data, period=14, stddev=2):
    data = convert_to_numpy(data)    
    return ti.bbands(data, period, stddev)


def wad(high_data, low_data, close_data, use_series=False):
    if check_series(high_data) or check_series(low_data) or check_series(close_data):
        use_series = True
    high_data = convert_to_numpy(high_data)
    low_data = convert_to_numpy(low_data)
    close_data = convert_to_numpy(close_data)
    wad = ti.wad(high_data, low_data, close_data)
    return pd.Series(wad) if use_series else wad


def wilders(data, period=50, use_series=False):
    if check_series(data):
        use_series = True
    data = convert_to_numpy(data)
    wilders = ti.wilders(data, period)
    return pd.Series(wilders) if use_series else wilders


def willr(high_data, low_data, close_data, period=50, use_series=False):
    if check_series(high_data) or check_series(low_data) or check_series(close_data):
        use_series = True
    high_data = convert_to_numpy(high_data)
    low_data = convert_to_numpy(low_data)
    close_data = convert_to_numpy(close_data)
    willr = ti.willr(high_data, low_data, close_data, period)
    return pd.Series(willr) if use_series else willr


def true_range(high_data, low_data, close_data, use_series=False):
    if check_series(high_data) or check_series(low_data) or check_series(close_data):
        use_series = True
    high_data = convert_to_numpy(high_data)
    low_data = convert_to_numpy(low_data)
    close_data = convert_to_numpy(close_data)
    tr = ti.tr(high_data, low_data, close_data)
    return pd.Series(tr) if use_series else tr


def average_true_range(high_data, low_data, close_data, period=50, use_series=False):
    if check_series(high_data) or check_series(low_data) or check_series(close_data):
        use_series = True
    high_data = convert_to_numpy(high_data)
    low_data = convert_to_numpy(low_data)
    close_data = convert_to_numpy(close_data)
    atr = ti.atr(high_data, low_data, close_data, period=period)
    return pd.Series(atr) if use_series else atr

