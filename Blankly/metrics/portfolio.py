import pandas as pd
import numpy as np


def cagr(start_value, end_value, years):
    return (end_value / start_value) ** (1 / years)


def cum_returns(start_value, end_value):
    return (start_value - end_value) / start_value


def sortino(returns, n=252, risk_free_rate=None):
    returns = pd.Series(returns)
    if risk_free_rate:
        mean = returns.mean() - risk_free_rate
    else:
        mean = returns.mean()
    std_neg = returns[returns < 0].std() 
    return mean / std_neg * np.sqrt(n)


def sharpe(returns, n=252, risk_free_rate=None):
    returns = pd.Series(returns)
    if risk_free_rate:
        mean = returns.mean() - risk_free_rate
    else:
        mean = returns.mean()
    std = returns.std() 
    return mean / std * np.sqrt(n)


def calmar(returns, n=252):
    return_series = pd.Series(returns)
    return return_series.mean() * np.sqrt(n) / abs(max_drawdown(return_series))


def volatility(returns, n=None):
    return np.std(returns) * np.sqrt(n) if n else np.std(returns)


def variance(returns, n=None):
    return np.var(returns) * np.sqrt(n) if n else np.var(returns)


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
    return_series = pd.Series(returns)
    comp_ret = (return_series+1).cumprod()
    peak = comp_ret.expanding(min_periods=1).max()
    dd = (comp_ret/peak)-1
    return dd.min()

