import time
import Blankly


class Bot(Blankly.BlanklyBot):
    def __init__(self):
        super().__init__()

    def main(self, args=None):
        """
        Main function to write the trading logic
        """
        # Use this to get IDE autofill
        assert isinstance(self.Interface, Blankly.Interface)
        assert isinstance(self.Ticker_Manager, Blankly.TickerManager)

        # Add a heartbeat example to report to GUI
        self.update_state("Heartbeat", 0)

        # Dataframe price history
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


if __name__ == "__main__":
    """
    Easily setup and run a model on any exchange
    """

    # This creates an authenticated exchange. Now we can append models.
    exchange = Blankly.Coinbase_Pro()
    # Imagine this:
    #   Coinbase Pro <-- Choosing to assign this bot to this exchange
    #   Kraken
    #   Binance

    # Create the bot and add it to run as a coinbase_pro bitcoin model.
    bot = Bot()
    exchange.append_model(bot, "GRT")
    # Imagine this:
    #   Coinbase Pro:
    #       Bitcoin
    #       Ethereum
    #       Stellar
    #       The Graph <-- Added to the data from this currency

    # Begins running the main() function of the model on a different process
    exchange.start_models()
    # Imagine this:
    #   Coinbase Pro:
    #       Bitcoin
    #       Ethereum
    #       Stellar
    #       The Graph <-- Bot <-- Asking to start

    # Now other processes can be created or just continue with this one.
    while True:
        # Print the state every 2 seconds
        state = exchange.get_currency_state("GRT")
        Blankly.Utils.pretty_print_JSON(state)
        time.sleep(1)
