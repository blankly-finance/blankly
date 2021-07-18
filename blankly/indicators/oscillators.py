"""
    Oscillator wrappers
    Copyright (C) 2021 Brandon Fan

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from typing import Any

import numpy as np
import pandas as pd
import tulipy as ti

from blankly.indicators.utils import check_series, convert_to_numpy


def rsi(data: Any, period: int = 14, round_rsi: bool = False, use_series=False) -> np.array:
    """ Implements RSI Indicator """
    if check_series(data):
        use_series = True
    data = convert_to_numpy(data)
    rsi_values = ti.rsi(data, period)
    if round_rsi:
        rsi_values = np.round(rsi_values, 2)
    return pd.Series(rsi_values) if use_series else rsi_values


def aroon_oscillator(high_data: Any, low_data: Any, period=14, use_series=False):
    if check_series(high_data) or check_series(low_data):
        use_series = True
    high_data = convert_to_numpy(high_data)
    low_data = convert_to_numpy(low_data)
    aroonsc = ti.aroonosc(high_data, low_data, period=period)
    return pd.Series(aroonsc) if use_series else aroonsc


def chande_momentum_oscillator(data, period=14, use_series=False):
    if check_series(data):
        use_series = True
    data = convert_to_numpy(data)
    cmo = ti.cmo(data, period)
    return pd.Series(cmo) if use_series else cmo


def absolute_price_oscillator(data, short_period=12, long_period=26, use_series=False):
    if check_series(data):
        use_series = True
    data = convert_to_numpy(data)
    apo = ti.apo(data, short_period, long_period)
    return pd.Series(apo) if use_series else apo


def percentage_price_oscillator(data, short_period=12, long_period=26, use_series=False):
    if check_series(data):
        use_series = True
    data = convert_to_numpy(data)
    ppo = ti.ppo(data, short_period, long_period)
    return pd.Series(ppo) if use_series else ppo


def stochastic_oscillator(high_data, low_data, close_data, pct_k_period=14, pct_k_slowing_period=3, pct_d_period=3,
                          use_series=False):
    if check_series(high_data) or check_series(low_data) or check_series(close_data):
        use_series = True
    high_data = convert_to_numpy(high_data)
    low_data = convert_to_numpy(low_data)
    close_data = convert_to_numpy(close_data)
    stoch = ti.stoch(high_data, low_data, close_data, pct_k_period, pct_k_slowing_period, pct_d_period)
    return pd.Series(stoch) if use_series else stoch


def stochastic_rsi(data, period=14, smooth_pct_k=3, smooth_pct_d=3):
    """ Calculates Stochoastic RSI Courteous of @lukazbinden
    :param data:
    :param period:
    :param smooth_pct_k:
    :param smooth_pct_d:
    :return:
    """
    # Calculate RSI
    rsi_values = rsi(data, period=period, round_rsi=False)

    # Calculate StochRSI
    rsi_values = pd.Series(rsi_values)
    stochrsi = (rsi_values - rsi_values.rolling(period).min()) / (
                rsi_values.rolling(period).max() - rsi_values.rolling(period).min())
    stochrsi_K = stochrsi.rolling(smooth_pct_k).mean()
    stochrsi_D = stochrsi_K.rolling(smooth_pct_d).mean()

    return round(rsi_values, 2), round(stochrsi_K * 100, 2), round(stochrsi_D * 100, 2)
