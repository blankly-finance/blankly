import Blankly
import time


def price_event(price, product_id):
    paper_trade_interface.market_order(product_id, 'buy', 100)


if __name__ == "__main__":
    """
    Authenticate
    """
    print("Authenticating...")
    # Create an authenticated coinbase pro object
    coinbase_pro = Blankly.Coinbase_Pro()

    # Wrap the coinbase pro object with a paper trade object so that no orders go through
    paper_trade = Blankly.PaperTrade(coinbase_pro.get_interface())

    # Get the interface so it can be used above to trade
    paper_trade_interface = paper_trade.get_interface()

    """
    Download price data
    """
    print("Downloading...")
    # You can delete this section up to the backtest section if you already downloaded the prices

    hist = paper_trade_interface.get_product_history('BTC-USD',
                                                     time.time() - Blankly.time_builder.build_day() * 20,  # 20 days before now
                                                     time.time(),  # To now
                                                     Blankly.time_builder.build_hour())  # At one hour resolution

    # Optionally save the prices instead of downloading each time. The price_data argument supports a path
    # price_path = './backtesting_data.csv'
    # hist.to_csv(price_path)

    """
    Backtest
    """
    print("Backtesting...")
    # Set up & run the backtest
    print(paper_trade.backtest(price_data=hist,
                               asset_id='BTC-USD',
                               price_event=price_event,
                               interval='2m'
                               ))
