import pandas as pd
import numpy as np
from datetime import datetime
import pytz
from dateutil.relativedelta import relativedelta
import Blankly.metrics as metrics


def cagr(backtest_data):
    account_values = backtest_data['resampled_account_value']
    start = datetime.fromtimestamp(account_values[0]['time'], tz=pytz.utc)
    end = datetime.fromtimestamp(account_values[-1]['time'], tz=pytz.utc)
    years = relativedelta(start, end).years
    return metrics.cagr(account_values[0], account_values[-1], years)
def cum_returns(backtest_data):
    account_values = backtest_data['resampled_account_value']
    return metrics.cum_returns(account_values[0], account_values[-1])

def sortino(backtest_data):
    # TODO: Need to pass in the specific resolution
    # Defaulting to 1d
    returns = backtest_data['returns']['value']
    return metrics.sortino(returns)

def sharpe(backtest_data):
    # TODO: Need to pass in the specific resolution
    # Defaulting to 1d
    returns = backtest_data['returns']['value']
    return metrics.sharpe(returns)
def calmar(backtest_data):
    # TODO: Need to pass in the specific resolution
    # Defaulting to 1d
    returns = backtest_data['returns']['value']
    return metrics.calmar(returns)
def volatility(backtest_data):
    returns = backtest_data['returns']['value']
    return metrics.volatility(returns)

def variance(backtest_data):
    returns = backtest_data['returns']['value']
    return metrics.variance(returns)

def beta(backtest_data):
    # TODO: Need to pass in the specific resolution
    # Defaulting to 1d
    # Need to get some sort of baseline for this one...
    # Use SP500 as default for all of them (can we get this data?)
    # Or pick one of the assets as a baseline
    returns = backtest_data['returns']['value']
    return metrics.beta(returns)

def var(backtest_data):
    returns = backtest_data['returns']['value']
    account_values = backtest_data['resampled_account_value']
    return metrics.var(account_values[0], returns, 0.95)

def cvar(backtest_data):
    returns = backtest_data['returns']['value']
    account_values = backtest_data['resampled_account_value']
    return metrics.cvar(account_values[0], returns, 0.95)

def max_drawdown(backtest_data):
    returns = backtest_data['returns']['value']
    return metrics.max_drawdown()
