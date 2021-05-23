import numpy as np
import tulipy as ti

def ema(data, period=50) -> np.array:
    if type(data) == list:
        data = np.asarray(data)
    return ti.ema(data, period=period)

def vwma(data, volume_data, period=50):
    if type(data) == list:
        data = np.asarray(data)
    return ti.vwma(data, volume_data, period=period)

def wma(data, period=50) -> np.array:
    if type(data) == list:
        data = np.asarray(data)
    return ti.wma(data, period)


def zlema(data, period=50) -> np.array:
    if type(data) == list:
        data = np.asarray(data)
    return ti.zlema(data, period)


def sma(data, period=50) -> np.array:
    """
    Finding the moving average of a dataset
    Args:
        data: (list) A list containing the data you want to find the moving average of
        period: (int) How far each average set should be
    """
    if type(data) == list:
        data = np.asarray(data)
    return ti.sma(data, period=period)


def hma(data, period=50) -> np.array:
    if type(data) == list:
        data = np.asarray(data)
    return ti.hma(data, period)

def kaufman_adaptive_ma(data, period=50) -> np.array:
    if type(data) == list:
        data = np.asarray(data)
    return ti.kama(data, period)

def trima(data, period=50) -> np.array:
    if type(data) == list:
        data = np.asarray(data)
    return ti.trima(data, period)

def macd(data, short_period=12, long_period=26, signal_period=9) -> np.array:
    if type(data) == list:
        data = np.asarray(data)
    return ti.macd(data, short_period, long_period, signal_period)
