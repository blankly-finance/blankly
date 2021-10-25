"""
    General indicators & metrics for blankly
    Copyright (C) 2021  Brandon Fan

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

    Big thanks to John from Codearmo
"""

import numpy as np
import pandas as pd

from blankly.utils.utils import info_print


def cagr(start_value, end_value, years):
    if end_value < start_value:
        info_print('End Value less than Start Value makes CAGR meaningless, returning 0')
        return 0.0
    return (end_value / start_value) ** (1 / years) - 1


def cum_returns(start_value, end_value):
    return (end_value - start_value) / start_value


def sortino(returns, n=252, risk_free_rate=None):
    returns = pd.Series(returns)
    if risk_free_rate:
        mean = returns.mean() * n - risk_free_rate
    else:
        mean = returns.mean() * n
    std_neg = returns[returns < 0].std() * np.sqrt(n)
    return mean / std_neg


def sharpe(returns, n=252, risk_free_rate=None):
    returns = pd.Series(returns)
    if risk_free_rate:
        mean = returns.mean() * n - risk_free_rate
    else:
        mean = returns.mean() * n
    std = returns.std() * np.sqrt(n)
    return mean / std


def calmar(returns, n=252):
    return_series = pd.Series(returns)
    return return_series.mean() * n / abs(max_drawdown(return_series))


def volatility(returns, n=None):
    return np.std(returns) * np.sqrt(n) if n else np.std(returns)


def variance(returns, n=None):
    return np.nanvar(returns) * np.sqrt(n) if n else np.nanvar(returns)


def beta(returns, market_base_returns):
    m = np.matrix([returns, market_base_returns])
    return np.cov(m)[0][1] / np.std(market_base_returns)


def var(initial_value, returns, alpha: float):
    returns_sorted = np.sort(returns)
    index = int(alpha * len(returns_sorted))
    return initial_value * abs(returns_sorted[index])


def cvar(initial_value, returns, alpha):
    returns_sorted = np.sort(returns)
    index = int(alpha * len(returns_sorted))
    sum_var = returns_sorted[0]
    for i in range(1, index):
        sum_var += returns_sorted[i]
    return initial_value * abs(sum_var / index)


def max_drawdown(returns):
    returns = pd.Series(returns)
    cumulative = (returns + 1).cumprod()
    peak = cumulative.expanding(min_periods=1).max()
    dd = (cumulative / peak) - 1
    return dd.min()
