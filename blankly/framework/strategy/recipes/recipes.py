import blankly


def golden_cross(ticker, interface: blankly.Interface, state: StrategyState):
    resolution: str = state.resolution  # get the resolution that this price event is stored at
    variables = state.__variables  # each price event has it's own local variable state

    account = interface.account  # get account holdings

    historical_prices = blankly.historical(ticker, 50, resolution=resolution)
    sma50 = blankly.analysis.calculate_sma(historical_prices, window=50)[
        -1]  # last 50 day sma value is the value we want

    if price > sma50 and variables['order_submitted']:
        variables['order_submitted'] = True
        interface.market_order(ticker, 'buy', account.cash * 0.25)
    elif price < sma50:  # only sell if there's an open position
        variables['order_submitted'] = False
        stocks_available = account.holdings[ticker].available * 0.5  # sell 50% of available sures
        interface.market_order(ticker, 'sell', stocks_available)


def rsi(price, ticker, interface: blankly.Interface, state: StrategyState):
    resolution: str = state.resolution  # get the resolution that this price event is stored at
    variables = state.__variables  # each price event has it's own local variable state

    account = interface.account  # get account holdings

    historical_prices = blankly.historical(ticker, 50, resolution=resolution)
    rsi = blankly.analysis.calculate_rsi(historical_prices)[-1]  # last 50 day sma value is the value we want

    if rsi > 70 and variables['order_submitted']:
        variables['order_submitted'] = True
        interface.market_order(ticker, 'buy', account.cash * 0.25)
    elif rsi < 30:  # only sell if there's an open position
        variables['order_submitted'] = False
        stocks_available = account.holdings[ticker].available * 0.5  # sell 50% of available sures
        interface.market_order(ticker, 'sell', stocks_available)
