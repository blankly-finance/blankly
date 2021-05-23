import numpy as np
import pandas as pd
import tulipy as ti

def bbands(data, period=14, stddev=2):
    if type(data) == list:
        data = np.asarray(data)
    return ti.bbands(data, period, stddev)

def wad(data, period=50):
    if type(data) == list:
        data = np.asarray(data)
    return ti.wad(data, period)

def wilders(data, period=50):
    if type(data) == list:
        data = np.asarray(data)
    return ti.wilders(data, period)

def willr(data, period=50):
    if type(data) == list:
        data = np.asarray(data)
    return ti.willr(data, period)

def true_range(high_data, low_data, close_data, period=50):
    if type(high_data) == list:
        high_data = np.asarray(high_data)
    if type(low_data) == list:
        low_data = np.asarray(low_data)
    if type(close_data) == list:
        close_data = np.asarray(close_data)
    return ti.tr(high_data, low_data, close_data, period=period)

def average_true_range(high_data, low_data, close_data, period=50):
    if type(high_data) == list:
        high_data = np.asarray(high_data)
    if type(low_data) == list:
        low_data = np.asarray(low_data)
    if type(close_data) == list:
        close_data = np.asarray(close_data)
    return ti.atr(high_data, low_data, close_data, period=period)

