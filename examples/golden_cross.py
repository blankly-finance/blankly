from blankly import Strategy, StrategyState, Interface
from blankly import Alpaca
from blankly.utils import trunc
from blankly.indicators import sma


def init(symbol, state: StrategyState):
    interface: Interface = state.interface
    resolution = state.resolution
    variables = state.variables
    # initialize the historical data
    variables['history'] = interface.history(symbol, 800, resolution, end_date=state.time, return_as='deque')['close']
    variables['owns_position'] = False


def price_event(price, symbol, state: StrategyState):
    interface: Interface = state.interface
    variables = state.variables

    variables['history'].append(price)

    sma200 = sma(variables['history'], period=200)
    # match up dimensions
    sma50 = sma(variables['history'], period=50)[-len(sma200):]
    diff = sma200 - sma50
    slope_sma50 = (sma50[-1] - sma50[-5]) / 5  # get the slope of the last 5 SMA50 Data Points
    prev_diff = diff[-2]
    curr_diff = diff[-1]
    is_cross_up = slope_sma50 > 0 and curr_diff >= 0 and prev_diff < 0
    is_cross_down = slope_sma50 < 0 and curr_diff <= 0 and prev_diff > 0
    # comparing prev diff with current diff will show a cross
    if is_cross_up and not variables['owns_position']:
        interface.market_order(symbol, 'buy', interface.cash)
        variables['owns_position'] = True
    elif is_cross_down and variables['owns_position']:
        # use strategy.base_asset if on CoinbasePro or Binance
        curr_value = trunc(interface.account[symbol].available * price, 2)
        interface.market_order(symbol, 'sell', curr_value)
        variables['owns_position'] = False


alpaca = Alpaca()
s = Strategy(alpaca)
s.add_price_event(price_event, 'MSFT', resolution='1d', init=init)
s.backtest(initial_values={'USD': 10000}, to='2y')
