import Blankly
import time


def price_event(price, product_id):
    # Run this every "2 minutes" in the backtest
    paper_trade_interface.market_order(product_id, 'buy', 10)


if __name__ == "__main__":
    """
    Authenticate
    """
    print("Authenticating...")
    # Create an authenticated coinbase pro object
    coinbase_pro = Blankly.Coinbase_Pro()

    # Wrap the coinbase pro object with a paper trade object so that no orders go through
    paper_trade = Blankly.PaperTrade(coinbase_pro)

    # Get the interface so it can be used above to trade
    paper_trade_interface = paper_trade.get_interface()

    """
    Download price data
    """
    print("Downloading...")
    hist = paper_trade_interface.get_product_history('BTC-USD',
                                                     time.time() - Blankly.time_builder.build_day() * 3,  # 3 days before now
                                                     time.time(),  # To now
                                                     Blankly.time_builder.build_hour())  # At one hour resolution

    # Optionally save the prices instead of downloading each time. The price_data argument supports a path
    # price_path = './backtesting_data.csv'
    # hist.to_csv(price_path)
    """
    Backtest
    """
    print("Backtesting...")
    # Add the price data to the backtest
    paper_trade.append_backtest_price_data(asset_id='BTC-USD', price_data=hist)

    # Add the price event to the backtest
    paper_trade.append_backtest_price_event(price_event, 'BTC-USD', '2m')

    # Run the backtest
    print(paper_trade.backtest())
