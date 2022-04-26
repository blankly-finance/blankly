import blankly


def price_event(price, symbol, state: blankly.StrategyState):
    """ This function will give an updated price every 15 seconds from our definition below """
    state.variables.history.append(price)

    rsi = blankly.indicators.rsi(state.variables.history)
    current_position = state.interface.account[state.base_asset].available

    if rsi[-1] < 30 and not current_position:
        # Dollar cost average buy
        buy = blankly.trunc(state.interface.cash / price, state.variables.precision)
        state.interface.market_order(symbol, side='buy', size=buy)

    elif rsi[-1] > 70 and current_position:
        # Sell our position
        state.interface.market_order(symbol, side='sell', size=current_position)


def init(symbol, state: blankly.StrategyState):
    # Download price data to give context to the algo
    state.variables.history = state.interface.history(symbol, to=150, return_as='deque',
                                                      resolution=state.resolution)['close']

    # Get the max precision for this symbol from the API
    increment = next(product['base_increment']
                     for product in state.interface.get_products()
                     if product['symbol'] == symbol)
    state.variables.precision = blankly.utils.increment_to_precision(increment)


if __name__ == "__main__":
    # Authenticate EXCHANGE_NAME strategy
    exchange = blankly.EXCHANGE_CLASS()

    # Use our strategy helper on EXCHANGE_NAME
    strategy = blankly.Strategy(exchange)

    # Run the price event function every time we check for a new price - by default that is 15 seconds
    strategy.add_price_event(price_event, symbol='SYMBOL', resolution='1d', init=init)

    # Start our strategy, or run a backtest if this script is run locally.
    if blankly.is_deployed:
        strategy.start()
    else:
        strategy.backtest(to='1y', initial_values={'USD': 10000})
