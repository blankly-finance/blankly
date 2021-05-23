import tulipy as ti
import numpy as np

def stdev_period(data, period=14) -> np.array:
    return ti.stddev(data, period)

def var_period(data, period=14) -> np.array:
    return ti.var(data, period)

def stderr_period(data, period=14) -> np.array:
    return ti.stderr(data, period)

def min_period(data, period) -> np.array:
    if type(data) == list:
        data = np.asarray(data)
    return ti.min(data, period)

def max_period(data, period) -> np.array:
    if type(data) == list:
        data = np.asarray(data)
    return ti.max(data, period)