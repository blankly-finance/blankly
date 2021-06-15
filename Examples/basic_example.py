import Blankly


def price_event(price, currency_pair):
    """
    This function will run every time we check for a new price - defined below
    """
    print("New price event: " + str(price) + " on " + str(currency_pair) + ".")


if __name__ == "__main__":
    # Authenticate coinbase pro strategy
    coinbase_pro = Blankly.Coinbase_Pro()

    # Define our interface in case we want to make our own API calls
    interface = coinbase_pro.get_interface()

    # Use our strategy helper on coinbase pro
    coinbase_strategy = Blankly.Strategy(coinbase_pro)

    # Run the price event function every time we check for a new price - by default that is 15 seconds
    coinbase_strategy.add_price_event(price_event, currency_pair='BTC-USD', resolution='15s')
    coinbase_strategy.add_price_event(price_event, currency_pair='LINK-USD', resolution='15s')
    coinbase_strategy.add_price_event(price_event, currency_pair='ETH-BTC', resolution='15s')

    # Start the strategy. This will begin each of the price event ticks
    coinbase_strategy.start()
