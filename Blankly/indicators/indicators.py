from Blankly.indicators.utils import convert_to_numpy
import numpy as np
import pandas as pd
import tulipy as ti

def bbands(data, period=14, stddev=2):
    data = convert_to_numpy(data)    
    return ti.bbands(data, period, stddev)

def wad(data, period=50, use_series=False):
    if type(data) == pd.Series:
        use_series = True
    data = convert_to_numpy(data)    
    wad = ti.wad(data, period)
    return pd.Series(wad) if use_series else wad

def wilders(data, period=50, use_series=False):
    if type(data) == pd.Series:
        use_series = True
    data = convert_to_numpy(data)    
    wilders = ti.wilders(data, period)
    return pd.Series(wilders) if use_series else wilders

def willr(data, period=50, use_series=False):
    if type(data) == pd.Series:
        use_series = True
    data = convert_to_numpy(data)    
    willr = ti.willr(data, period)
    return pd.Series(willr) if use_series else willr

def true_range(high_data, low_data, close_data, period=50, use_series=False):
    if type(high_data) == pd.Series or type(low_data) == pd.Series or type(close_data) == pd.Series:
        use_series = True
    high_data = convert_to_numpy(high_data)
    low_data = convert_to_numpy(low_data)
    close_data = convert_to_numpy(close_data)
    tr = ti.tr(high_data, low_data, close_data, period=period)
    return pd.Series(tr) if use_series else tr

def average_true_range(high_data, low_data, close_data, period=50, use_series=False):
    if type(high_data) == pd.Series or type(low_data) == pd.Series or type(close_data) == pd.Series:
        use_series = True
    high_data = convert_to_numpy(high_data)
    low_data = convert_to_numpy(low_data)
    close_data = convert_to_numpy(close_data)
    atr = ti.atr(high_data, low_data, close_data, period=period)
    return pd.Series(atr) if use_series else atr

