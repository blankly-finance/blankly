import numpy as np
import pandas as pd
from statistics import mean


def calculate_ema(data, window=50, smoothing=2) -> list:
    ema = pd.Series(data).ewm(min_periods=window, alpha=smoothing).mean()
    return ema.tolist()


def calculate_rsi(data, window=14):
    delta = pd.Series(data).diff()
    days_up, days_down = delta.copy(), delta.copy()
    days_up[days_up < 0] = 0
    days_down[days_down > 0] = 0

    roll_up = pd.rolling_mean(days_up, window)
    roll_down = pd.rolling_mean(days_down, window).abs()

    return (roll_up / roll_down).tolist()


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
