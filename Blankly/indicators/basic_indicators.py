import numpy as np
import pandas as pd
from statistics import mean
import tulipy as ti

def ema(data, window=50) -> np.array:
    if type(data) == list:
        data = np.asarray(data)
    return ti.ema(data, period=window)


def rsi(data, period=14, round_rsi=True) -> np.array:
    """ Implements RSI Indicator """
    if type(data) == list:
        data = np.asarray(data)
    
    rsi_values = ti.rsi(data, period)
    return np.round(rsi, 2) if round_rsi else rsi

def stochastic_rsi(data, period=14, smoothK=3, smoothD=3):
    """ Calculates Stochoastic RSI Courteous of @lukazbinden
    :param ohlc:
    :param period:
    :param smoothK:
    :param smoothD:
    :return:
    """
    # Calculate RSI
    rsi_values = rsi(data, period=period, round_rsi=False)

    # Calculate StochRSI
    rsi_values = pd.Series(rsi_values)
    stochrsi  = (rsi - rsi.rolling(period).min()) / (rsi.rolling(period).max() - rsi.rolling(period).min())
    stochrsi_K = stochrsi.rolling(smoothK).mean()
    stochrsi_D = stochrsi_K.rolling(smoothD).mean()

    return round(rsi_values, 2).tolist(), round(stochrsi_K * 100, 2).tolist(), round(stochrsi_D * 100, 2).tolist()


def sma(data, window=50) -> np.array:
    """
    Finding the moving average of a dataset
    Args:
        data: (list) A list containing the data you want to find the moving average of
        window: (int) How far each average set should be
    """
    data = np.asarray(data)
    return ti.sma(data, period=window)
