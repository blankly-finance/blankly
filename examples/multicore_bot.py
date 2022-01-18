"""
    This file shows how multicore bots can be spawned & used to carry out intensive but separate tasks
"""

import time
import blankly
# Have feedback? Use this: https://forms.gle/4oAjG9MKRTYKX2hP9


class Bot(blankly.BlanklyBot):
    def main(self, args):
        """
        Main function to write any general analysis or bot management logic
        """
        # Create a demo ticker object. The price event function will run at every tick
        self.ticker_manager.create_ticker(callback=self.price_event)

        # Add a heartbeat example to report to GUI or main
        self.update_state("heartbeat", 0)

        # This will work on any supported exchange
        print("Interface call: " + str(self.interface.get_fees()))

        # You can also bypass the interface and make calls directly to the exchange:
        try:
            # Because this is direct, some exchanges have different commands, so this demo is wrapped in try/except
            print("Direct call: " + str(self.direct_calls.get_fees()))
        except AttributeError:
            # If it doesn't have that function we just complain about it and move on
            print("Chosen exchange doesn't have that function")

        while True:
            # This demonstrates a way to change the state. This is just reporting to the main.
            current_heartbeat = self.get_state()["heartbeat"]
            self.update_state("heartbeat", current_heartbeat + 1)
            time.sleep(1)

    def price_event(self, tick):
        """
        This is called on price update events from the ticker feeds
        """
        # Example of updating the price state for the GUI
        self.update_state("Price", str(tick["price"]))
        # Show these new ticks to the console
        print("New price tick at: " + str(tick["price"]))


if __name__ == "__main__":
    """
    Easily setup and run a model on any supported exchange
    """

    # This creates an authenticated exchange and chooses the first portfolio in the keys.json file
    # You can use portfolio_name="my cool portfolio" if want a certain one
    portfolio = blankly.CoinbasePro()  # You could also use blankly.Binance()

    # Create the bot and add it to run as a coinbase_pro bitcoin model.
    bot = Bot()
    portfolio.append_model(model=bot, symbol="BTC-USD", args=[])

    # This starts the main() function of the model and puts it on a different process (computer core)
    # The main() function is in the class above
    portfolio.start_models(symbol="BTC-USD")

    # Now other processes can be created or just continue with this one.
    while True:
        # Print the state from the model we just started every second
        state = portfolio.get_full_state("BTC-USD")
        blankly.utils.pretty_print_json(state)
        time.sleep(1)
