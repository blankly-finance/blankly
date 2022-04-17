"""
    This simulates a macd strategy running once a day across many stocks
"""

from blankly import Strategy, StrategyState, Interface
from blankly import Alpaca
from blankly.utils import trunc
from blankly.indicators import macd

SHORT_PERIOD = 12
LONG_PERIOD = 26
SIGNAL_PERIOD = 9


def init(symbol, state: StrategyState):
    interface = state.interface
    resolution = state.resolution
    variables = state.variables
    # initialize the historical data
    variables['history'] = interface.history(symbol, 800, resolution, return_as='deque')['close']
    variables['short_period'] = SHORT_PERIOD
    variables['long_period'] = LONG_PERIOD
    variables['signal_period'] = SIGNAL_PERIOD
    variables['has_bought'] = False


def price_event(price, symbol, state: StrategyState):
    interface: Interface = state.interface
    # allow the resolution to be any resolution: 15m, 30m, 1d, etc.
    variables = state.variables

    variables['history'].append(price)
    macd_res, macd_signal, macd_histogram = macd(variables['history'], 
                                                 short_period=variables['short_period'],
                                                 long_period=variables['long_period'],
                                                 signal_period=variables['signal_period'])

    slope_macd = (macd_res[-1] - macd_res[-5]) / 5  # get the slope of the last 5 MACD_points
    prev_macd = macd_res[-2]
    curr_macd = macd_res[-1]
    curr_signal_macd = macd_signal[-1]

    # We want to make sure this works even if curr_macd does not equal the signal MACD
    is_cross_up = slope_macd > 0 and curr_macd >= curr_signal_macd > prev_macd

    is_cross_down = slope_macd < 0 and curr_macd <= curr_signal_macd < prev_macd
    if is_cross_up:
        # If there is a buy signal, buy with 40% of cash available (that 40% has to be more than 10 dollars though)
        cash = trunc(interface.cash * .4, 2)
        if cash > 10:
            interface.market_order(symbol, 'buy', int(cash/price))
            variables['has_bought'] = True
    elif is_cross_down and variables['has_bought']:
        # Sell all of the position. We also have to own a position after buying
        interface.market_order(symbol, 'sell', int(interface.account[symbol].available))
        variables['has_bought'] = False


if __name__ == "__main__":
    alpaca = Alpaca()
    s = Strategy(alpaca)

    # Add a bunch of stocks to watch for 2 years
    s.add_price_event(price_event, 'SNAP', resolution='1d', init=init)
    s.add_price_event(price_event, 'PBFX', resolution='1d', init=init)
    s.add_price_event(price_event, 'NCLH', resolution='1d', init=init)

    s.add_price_event(price_event, 'CRBP', resolution='1d', init=init)
    s.add_price_event(price_event, 'D', resolution='1d', init=init)
    s.add_price_event(price_event, 'GME', resolution='1d', init=init)

    print(s.backtest(initial_values={'USD': 10000}, to='2y'))
