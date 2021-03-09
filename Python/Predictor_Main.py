from multiprocessing import Process, Manager
import time
from API_Interface import APIInterface



class Predictor:
    def __init__(self, exchange_type, coin, user_preferences, initial_state, interface):
        # Shared variables with the processing a manager
        self.__state = Manager().dict(initial_state)
        self.__exchange_type = exchange_type
        self.__currency = coin
        self.__user_preferences = user_preferences
        self.Interface = interface

        # If the start is called again, this will make sure multiple processes don't start
        self.__is_running = False

        # Coin id is the currency and the market its on
        self.__coin_id = coin + "-" + user_preferences["settings"]["base_currency"]
        # Create the ticker for this kind of currency. Callbacks will occur in the "price_event" function
        self.__ticker = self.Interface.create_ticker(self, self.__coin_id)

    # Make sure the process knows that this model is on, turning this off could result in many threads
    def is_running(self):
        return self.__is_running

    """
    Begins the relevant process
    """
    def run(self, args):
        # Start the process
        if (args == None):
            p = Process(target=self.main)
        else:
            p = Process(target=self.main, args=args)
        self.__is_running = True
        p.start()

    """
    State functions for writing to the GUI
    """
    def get_state(self):
        return self.__state

    def update_state(self, key, value):
        self.__state[key] = value

    def remove_key(self, key):
        self.__state.pop(key)

    """
    Is called on price event updates by the ticker
    """
    def price_event(self, tick):
        # Example of updating the price state for the GUI
        self.update_state("Price", tick["price"])
        print(tick)


    def main(self, args=None):
        assert isinstance(self.Interface, APIInterface)

        # Add a heartbeat example to report to GUI
        self.update_state("Heartbeat", 0)
        # Example on how to interact with API
        print(self.Interface.get_currencies())
        while True:
            """ Demo interface call """
            self.update_state("Heartbeat", self.get_state()["Heartbeat"]+1)
            time.sleep(1)
