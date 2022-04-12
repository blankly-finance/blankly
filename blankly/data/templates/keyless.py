import requests
import blankly


def price_event(price, symbol, state: blankly.StrategyState):
    """ This function will give an updated price every 15 seconds from our definition below """
    state.variables['history'].append(price)
    rsi = blankly.indicators.rsi(state.variables['history'])
    if rsi[-1] < 30 and not state.variables['owns_position']:
        # Dollar cost average buy
        buy = int(state.interface.cash / price)
        state.interface.market_order(symbol, side='buy', size=buy)
        state.variables['owns_position'] = True
    elif rsi[-1] > 70 and state.variables['owns_position']:
        # Dollar cost average sell
        curr_value = state.interface.account[state.base_asset].available
        state.interface.market_order(symbol, side='sell', size=int(curr_value))
        state.variables['owns_position'] = False


def init(symbol, state: blankly.StrategyState):
    # Download price data to give context to the algo
    state.variables['history'] = state.interface.history(symbol, to=150, return_as='deque',
                                                         resolution=state.resolution)['close']
    state.variables['owns_position'] = False


if __name__ == "__main__":
    # This downloads an example CSV
    data = requests.get('https://firebasestorage.googleapis.com/v0/b/blankly-6ada5.appspot.com/o/price_examples.csv?'
                        'alt=media&token=3f3c37ee-a87b-46b0-b145-077c0e25254b').text
    with open('./price_examples.csv', 'w') as file:
        file.write(data)

    # Run on the keyless exchange, starting at 100k
    exchange = blankly.KeylessExchange('./price_examples.csv', initial_account_values={'USD': 100000})

    # Use our strategy helper
    strategy = blankly.Strategy(exchange)

    # Make the price event function above run every day
    strategy.add_price_event(price_event, symbol='BTC-USD', resolution='1d', init=init)

    # Backtest the strategy
    results = strategy.backtest(start_date=1568547200, end_date=1642982400)
    print(results)
