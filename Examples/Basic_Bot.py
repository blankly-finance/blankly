from multiprocessing import Process, Manager
import time
import Blankly


class Bot:
    def __init__(self):
        """ Initialize state variables """
        # If the start is called again, this will make sure multiple processes don't start
        self.__is_running = False
        self.__state = {}
        self.__exchange_type = ""
        self.__currency = ""
        self.__user_preferences = {}
        self.Interface = None
        self.__coin_id = ""
        self.__ticker = None

    """ This function is populated by the exchange. """
    def setup(self, exchange_type, coin, user_preferences, initial_state, interface):
        # Shared variables with the processing a manager
        self.__state = Manager().dict(initial_state)
        self.__exchange_type = exchange_type
        self.__currency = coin
        self.__user_preferences = user_preferences
        self.Interface = interface

        # Coin id is the currency and which market its on
        self.__coin_id = coin + "-" + user_preferences["settings"]["base_currency"]
        # Create the ticker for this kind of currency. Callbacks will occur in the "price_event" function
        self.__ticker = self.Interface.create_ticker(self, self.__coin_id)

    # Make sure the process knows that this model is on, removing this off could result in many threads
    def is_running(self):
        return self.__is_running

    """ Called by GUI when the user starts the model """
    def run(self, args):
        # Start the process
        if args is None:
            p = Process(target=self.main)
        else:
            p = Process(target=self.main, args=args)
        self.__is_running = True
        p.start()

    """ State getters and setters for writing to the GUI or as state updates """
    def get_state(self):
        return self.__state

    def update_state(self, key, value):
        self.__state[key] = value

    def remove_key(self, key):
        self.__state.pop(key)

    """ Is called on price event updates by the ticker """
    def price_event(self, tick):
        # Example of updating the price state for the GUI
        self.update_state("Price", tick["price"])
        print(tick)

    """ Main function to write the trading loop """
    def main(self, args=None):
        assert isinstance(self.Interface, Blankly.APIInterface)

        # Add a heartbeat example to report to GUI
        self.update_state("Heartbeat", 0)

        # Example on how to interact with API
        print(self.Interface.get_currencies())
        while True:
            """ Demo interface call """
            self.update_state("Heartbeat", self.get_state()["Heartbeat"] + 1)
            time.sleep(1)


if __name__ == "__main__":
    # Define preferences, base currency is needed for the trading.
    user_preferences = {
        # Example portion of the settings to make a minimum example
        "settings": {
            "base_currency": "USD"
        }
    }

    # Keys file contains authentication keys
    import Keys
    auth = [Keys.API_KEY, Keys.API_SECRET, Keys.API_PASS]

    # This creates an authenticated exchange. Now we can append models.
    exchange = Blankly.Coinbase_Pro(name="API Exchange", user_preferences=user_preferences, auth=auth)

    # Create the bot and add it to run as a coinbase_pro bitcoin model.
    bot = Bot()
    exchange.append_model(bot, "GRT")

    # Begins running the main() function of the model on a different process
    exchange.start_models()

    # Now other processes can be created or just continue with this one.
    while True:
        # Print the state every second
        print(exchange.get_currency_state("GRT"))
        time.sleep(2)
