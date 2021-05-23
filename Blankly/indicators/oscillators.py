import numpy as np
import pandas as pd
import tulipy as ti

def rsi(data, period=14, round_rsi=True) -> np.array:
    """ Implements RSI Indicator """
    if type(data) == list:
        data = np.asarray(data)
    
    rsi_values = ti.rsi(data, period)
    return np.round(rsi_values, 2) if round_rsi else rsi

def aroon_oscillator(high_data, low_data, period=14):
    if type(high_data) == list:
        high_data = np.asarray(high_data)
    if type(low_data) == list:
        low_data = np.asarray(low_data)
    return ti.aroonosc(high_data, low_data, period=period)

def chande_momentum_oscillator(data, period=14):
    if type(data) == list:
        data = np.asarray(data)
    return ti.cmo(data, period)

def absolute_price_oscillator(data, short_period=12, long_period=26):
    if type(data) == list:
        data = np.asarray(data)
    return ti.apo(data, short_period, long_period)

def percentage_price_oscillator(data, short_period=12, long_period=26):
    if type(data) == list:
        data = np.asarray(data)
    return ti.ppo(data, short_period, long_period)

def stochastic_oscillator(high_data, low_data, close_data, pct_k_period=14, pct_k_slowing_period=3, pct_d_period=3):
    if type(high_data) == list:
        high_data = np.asarray(high_data)
    if type(low_data) == list:
        low_data = np.asarray(low_data)
    if type(close_data) == list:
        close_data = np.asarray(close_data)
    return ti.stoch(high_data, low_data, close_data, pct_k_period, pct_k_slowing_period, pct_d_period)


def stochastic_rsi(data, period=14, smooth_pct_k=3, smooth_pct_d=3):
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
    stochrsi_K = stochrsi.rolling(smooth_pct_k).mean()
    stochrsi_D = stochrsi_K.rolling(smooth_pct_d).mean()

    return round(rsi_values, 2).tolist(), round(stochrsi_K * 100, 2).tolist(), round(stochrsi_D * 100, 2).tolist()