"""
    Moving average function utils
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

import pandas as pd
import tulipy as ti

from blankly.indicators.utils import check_series, convert_to_numpy


def ema(data: Any, period: int = 50, use_series=False) -> Any:
    if check_series(data):
        use_series = True
    data = convert_to_numpy(data)
    ema = ti.ema(data, period=period)
    return pd.Series(ema) if use_series else ema


def vwma(data: Any, volume_data: Any, period: int = 50, use_series=False) -> Any:
    if check_series(data):
        use_series = True

    data = convert_to_numpy(data)
    volume_data = convert_to_numpy(volume_data).astype(float)

    vwma = ti.vwma(data, volume_data, period=period)
    return pd.Series(vwma) if use_series else vwma


def wma(data: Any, period: int = 50, use_series=False) -> Any:
    if check_series(data):
        use_series = True
    data = convert_to_numpy(data)
    wma = ti.wma(data, period)
    return pd.Series(wma) if use_series else wma


def zlema(data: Any, period: int = 50, use_series=False) -> Any:
    if check_series(data):
        use_series = True
    data = convert_to_numpy(data)
    zlema = ti.zlema(data, period)
    return pd.Series(zlema) if use_series else zlema


def sma(data: Any, period: int = 50, use_series=False) -> Any:
    """
    Finding the moving average of a dataset
    Args:
        data: (list) A list containing the data you want to find the moving average of
        period: (int) How far each average set should be
    """
    if check_series(data):
        use_series = True
    data = convert_to_numpy(data)
    sma = ti.sma(data, period=period)
    return pd.Series(sma) if use_series else sma


def hma(data: Any, period: int = 50, use_series=False) -> Any:
    if check_series(data):
        use_series = True
    data = convert_to_numpy(data)
    hma = ti.hma(data, period)
    return pd.Series(hma) if use_series else hma


def kaufman_adaptive_ma(data: Any, period: int = 50, use_series=False) -> Any:
    if check_series(data):
        use_series = True
    data = convert_to_numpy(data)
    kama = ti.kama(data, period)
    return pd.Series(kama) if use_series else kama


def trima(data: Any, period: int = 50, use_series=False) -> Any:
    if check_series(data):
        use_series = True
    data = convert_to_numpy(data)
    trima = ti.trima(data, period)
    return pd.Series(trima) if use_series else trima


def macd(data: Any, short_period: int = 12, long_period: int = 26, signal_period: int = 9, use_series=False) -> Any:
    if check_series(data):
        use_series = True
    data = convert_to_numpy(data)
    macd, macd_signal, macd_histogram = ti.macd(data, short_period, long_period, signal_period)
    if use_series:
        df = pd.DataFrame({'macd': macd, 'macd_signal': macd_signal, 'macd_histogram': macd_histogram})
        return df
    return macd, macd_signal, macd_histogram
