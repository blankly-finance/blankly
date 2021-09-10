import blankly


def price_event(price, symbol, state: blankly.StrategyState):
    """ This function will give an updated price every 15 seconds from our definition below """
    state.variables['history'].append(price)
    rsi = blankly.indicators.rsi(state.variables['history'])
    if rsi[-1] < 30:
        # Dollar cost average buy
        print("buying...")
        state.interface.market_order(symbol, side='buy', funds=10)
    elif rsi[-1] > 70:
        # Dollar cost average sell
        print("selling...")
        state.interface.market_order(symbol, side='sell', funds=10)
    else:
        print("no action...")


def init(symbol, state: blankly.StrategyState):
    # Download price data to give context to the algo
    state.variables['history'] = state.interface.history(symbol, to='1y', return_as='list')['close']


if __name__ == "__main__":
    # Authenticate coinbase pro strategy
    coinbase_pro = blankly.CoinbasePro()

    # Use our strategy helper on coinbase pro
    coinbase_strategy = blankly.Strategy(coinbase_pro)

    # Run the price event function every time we check for a new price - by default that is 15 seconds
    coinbase_strategy.add_price_event(price_event, symbol='BTC-USD', resolution='1h', init=init)

    # Start the strategy. This will begin each of the price event ticks
    coinbase_strategy.start()
    # Or backtest using this
    # coinbase_strategy.backtest(to='1y', initial_values={'USD': 100000, 'BTC': 2})
