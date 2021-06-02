import Blankly


def price_event(price, product_id):
    # Run this every "2 minutes" in the backtest
    strategy.Interface.market_order(product_id, 'buy', 10)


if __name__ == "__main__":
    """
    Authenticate
    """
    print("Authenticating...")
    # Create an authenticated coinbase pro object
    coinbase_pro = Blankly.Coinbase_Pro()

    # Create a strategy object
    strategy = Blankly.Strategy(coinbase_pro)

    """
    Backtest
    """
    print("Backtesting...")
    # Add the function to the strategy class
    strategy.add_price_event(price_event, 'BTC-USD', resolution='1h')

    # The backtest function will now turn our strategy class into a class that can be backtested
    print(strategy.backtest(to='1y'))
