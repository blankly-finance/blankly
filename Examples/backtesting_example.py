import Blankly
import time


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
    Download price data
    """
    print("Downloading...")
    hist = strategy.Interface.get_product_history('BTC-USD',
                                                  time.time() - Blankly.time_builder.build_day() * 3,
                                                  # 3 days before now
                                                  time.time(),  # To now
                                                  Blankly.time_builder.build_hour())  # At one hour resolution
    # Optionally save the prices instead of downloading each time. The price_data argument supports a path
    # price_path = './backtesting_data.csv'
    # hist.to_csv(price_path)
    """
    Backtest
    """
    print("Backtesting...")
    # Add the function to the strategy class
    strategy.add_price_event(price_event, 'BTC-USD', resolution='2m')

    # The backtest function will now turn our strategy class into a class that can be backtested
    print(strategy.backtest(asset_id='BTC-USD', price_data=hist))
