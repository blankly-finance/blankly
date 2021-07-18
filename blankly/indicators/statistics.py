"""
    Statistics functions
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


def stddev_period(data, period=14, use_series=False) -> Any:
    if check_series(data):
        use_series = True
    data = convert_to_numpy(data)
    stddev = ti.stddev(data, period)
    return pd.Series(stddev) if use_series else stddev


def var_period(data, period=14, use_series=False) -> Any:
    if check_series(data):
        use_series = True
    data = convert_to_numpy(data)
    var = ti.var(data, period)
    return pd.Series(var) if use_series else var


def stderr_period(data, period=14, use_series=False) -> Any:
    if check_series(data):
        use_series = True
    data = convert_to_numpy(data)
    stderr = ti.stderr(data, period)
    return pd.Series(stderr) if use_series else stderr


def min_period(data, period, use_series=False) -> Any:
    if check_series(data):
        use_series = True
    data = convert_to_numpy(data)
    minimum = ti.min(data, period)
    return pd.Series(minimum) if use_series else minimum


def max_period(data, period, use_series=False) -> Any:
    if check_series(data):
        use_series = True
    data = convert_to_numpy(data)
    maximum = ti.max(data, period)
    return pd.Series(maximum) if use_series else maximum


def sum_period(data, period, use_series=False) -> Any:
    if check_series(data):
        use_series = True
    data = convert_to_numpy(data)
    maximum = ti.sum(data, period)
    return pd.Series(maximum) if use_series else maximum
