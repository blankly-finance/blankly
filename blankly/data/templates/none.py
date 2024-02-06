import blankly

if __name__ == "__main__":
    exchange = blankly.EXCHANGE_CLASS()
    strategy = blankly.Strategy(exchange)

    if blankly.is_deployed:
        strategy.start()
    else:
        strategy.backtest(to='1y', initial_values={'USD': 10000})
