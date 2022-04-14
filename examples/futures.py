import blankly


def price_event(price, symbol, state: blankly.FuturesStrategyState):
    state.interface.market_order(symbol, side='buy', position='short', size=1)


if __name__ == "__main__":
    # Authenticate Binance Futures exchange
    exchange = blankly.BinanceFutures()

    # Use our strategy helper on binance futures
    strategy = blankly.FuturesStrategy(exchange)

    strategy.add_price_event(price_event, symbol='BTC-USDT', resolution='1d')

    # Start the strategy. This will begin each of the price event ticks
    # strategy.start()
    # Or backtest using this:
    results = strategy.backtest(to='1M', initial_values={'USDT': 1000000})
    print(results)
