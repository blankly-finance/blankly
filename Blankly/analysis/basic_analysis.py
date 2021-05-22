import numpy as np
import pandas as pd
from statistics import mean


def calculate_ema(data, window=50, smoothing=2) -> list:
    ema = pd.Series(data).ewm(min_periods=window, alpha=smoothing).mean()
    return ema.tolist()


def calculate_rsi(data, period=14, round_rsi=True):
    """ Implements RSI Indicator, Courteous of Trading View and @lukazbinden"""
    delta = pd.Series(data).diff()
    up = delta.copy()
    up[up < 0] = 0
    up = pd.Series.ewm(up, alpha=1/period).mean()

    down = delta.copy()
    down[down > 0] = 0
    down *= -1
    down = pd.Series.ewm(down, alpha=1/period).mean()

    rsi = np.where(up == 0, 0, np.where(down == 0, 100, 100 - (100 / (1 + up / down))))

    return np.round(rsi, 2).tolist() if round_rsi else rsi.tolist()

def calculate_stochastic_rsi(data, period=14, smoothK=3, smoothD=3):
    """ Calculates Stochoastic RSI Courteous of @lukazbinden
    :param ohlc:
    :param period:
    :param smoothK:
    :param smoothD:
    :return:
    """
    # Calculate RSI
    rsi = calculate_rsi(data, period=period, round_rsi=False)

    # Calculate StochRSI
    rsi = pd.Series(rsi)
    stochrsi  = (rsi - rsi.rolling(period).min()) / (rsi.rolling(period).max() - rsi.rolling(period).min())
    stochrsi_K = stochrsi.rolling(smoothK).mean()
    stochrsi_D = stochrsi_K.rolling(smoothD).mean()

    return round(rsi, 2).tolist(), round(stochrsi_K * 100, 2).tolist(), round(stochrsi_D * 100, 2).tolist()


def average_recent(data, window=None) -> float:
    if window is None:
        return mean(data)
    return mean(data[-window:])


def calculate_sma(data, window=50, offset=False) -> list:
    """
    Finding the moving average of a dataset. Note that this removes the depth-1 points from the beginning of the set.
    Args:
        data: (list) A list containing the data you want to find the moving average of
        window: (int) How far each average set should be
        offset: (int) Append original data values to beginning of SMA for easy plotting or analysis involving
         equal lengths
    """
    # Cast pandas array to list for numpy
    try:
        data = data.tolist()
    except AttributeError:
        pass
    ret = np.cumsum(data, dtype=float)

    ret[window:] = ret[window:] - ret[:-window]
    avg_list = list(ret[window - 1:] / window)

    # Append the original data values to make the array lengths the same.
    if offset:
        difference = (len(data) - len(avg_list))
        avg_list = data[0:difference] + avg_list

    return avg_list
