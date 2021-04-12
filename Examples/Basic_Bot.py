import time
import Blankly
# Have feedback? Use this: https://forms.gle/4oAjG9MKRTYKX2hP9


class Bot(Blankly.BlanklyBot):
    def __init__(self):
        super().__init__()

    def main(self, args):
        """
        Main function to write the trading logic
        """
        # Use this to get IDE autofill
        assert isinstance(self.Interface, Blankly.Interface)
        assert isinstance(self.Ticker_Manager, Blankly.TickerManager)

        # Add a heartbeat example to report to GUI
        self.update_state("Heartbeat", 0)
        print(self.Interface.get_currencies())

        # Dataframe price history (commented because it takes time to run)
        # print(self.Interface.get_product_history(self.coin_id, 1611029486, 1616123507, 10000))
        print("Interface call: " + str(self.Interface.get_fees()))

        # You can also bypass the interface and make calls directly to the exchange:
        try:
            # Because this is direct, some exchanges have different commands, so this demo is wrapped in try/except
            print("Direct call: " + str(self.direct_calls.get_fees()))
        except AttributeError:
            print("Chosen exchange doesn't have that function")

        while True:
            # This demonstrates a way to change the state. The default script just reports the state on this currency.
            self.update_state("Heartbeat", self.get_state()["Heartbeat"] + 1)
            time.sleep(1)

    def price_event(self, tick):
        """
        Is called on price event updates by the ticker
        """
        # Example of updating the price state for the GUI
        self.update_state("Price", tick["price"])
        # Show these new ticks to the console
        print("New price tick at: " + tick["price"])

    def orderbook_event(self, tick):
        """
        Similar to the price_event function, this is called by orderbook updates
        """
        pass


if __name__ == "__main__":
    """
    Easily setup and run a model on any supported exchange
    """

    # This creates an authenticated exchange. Now we can append models.
    exchange = Blankly.Coinbase_Pro()
    # Imagine this:
    #   Coinbase Pro <-- Choosing to assign this bot to this exchange
    #   Kraken
    #   Binance

    # Create the bot and add it to run as a coinbase_pro bitcoin model.
    bot = Bot()
    exchange.append_model(bot, "BTC")
    # Imagine this:
    #   Coinbase Pro:
    #       Bitcoin <-- Added to the data from this currency
    #       Ethereum
    #       Stellar

    # Begins running the main() function of the model on a different process
    exchange.start_models()
    # Imagine this:
    #   Coinbase Pro:
    #       Bitcoin <-- Bot <-- Asking to start
    #       Ethereum
    #       Stellar

    # Now other processes can be created or just continue with this one.
    while True:
        # Print the state every 1 second
        state = exchange.get_full_state("BTC")
        Blankly.utils.pretty_print_JSON(state)
        time.sleep(1)
