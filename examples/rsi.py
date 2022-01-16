import blankly


def price_event(price, symbol, state: blankly.StrategyState):
    """ This function will give an updated price every 15 seconds from our definition below """
    state.variables['history'].append(price)
    rsi = blankly.indicators.rsi(state.variables['history'])
    if rsi[-1] < 30 and not state.variables['owns_position']:
        # Dollar cost average buy
        buy = blankly.trunc(state.interface.cash/price, 2)
        state.interface.market_order(symbol, side='buy', size=buy)
        state.variables['owns_position'] = True
    elif rsi[-1] > 70 and state.variables['owns_position']:
        # Dollar cost average sell
        curr_value = state.interface.account[state.base_asset].available
        state.interface.market_order(symbol, side='sell', size=curr_value)
        state.variables['owns_position'] = False


def init(symbol, state: blankly.StrategyState):
    # Download price data to give context to the algo
    state.variables['history'] = state.interface.history(symbol, to=150, return_as='deque',
                                                         resolution=state.resolution)['close']
    state.variables['owns_position'] = False


if __name__ == "__main__":
    # Authenticate coinbase pro strategy
    exchange = blankly.CoinbasePro()

    # Use our strategy helper on coinbase pro
    strategy = blankly.Strategy(exchange)

    # Run the price event function every time we check for a new price - by default that is 15 seconds
    strategy.add_price_event(price_event, symbol='BTC-USD', resolution='1d', init=init)

    # Start the strategy. This will begin each of the price event ticks
    # strategy.start()
    # Or backtest using this
    results = strategy.backtest(to='1y', initial_values={'USD': 10000})
    print(results)
