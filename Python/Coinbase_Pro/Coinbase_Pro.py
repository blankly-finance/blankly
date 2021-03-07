import cryptofeed, json
from Exchange import Exchange
from Predictor_Main import Predictor
from Coinbase_Pro.Coinbase_Pro_API import API


class Coinbase_Pro(Exchange):
    def __init__(self, name, user_preferences, auth):
        self.__calls = API(auth[0], auth[1], auth[2])

        initial_exchange_state = {
            "Value": 0,
            "Volume": 0
        }
        # Initialize the attached script
        self.model = Predictor("coinbase_pro", initial_exchange_state)
        Exchange.__init__(self, "coinbase_pro", name, user_preferences, self.model)
        self.get_state()

    def get_state(self):
        self.__state = self.__calls.getPortfolio()
        return self.__state

    """
    Portfolio state is the internal properties for the exchange block
    """
    def get_portfolio_state(self):
        self.get_state()
        self.__readable_state = {
        }
        for i in range(len(self.__state)):
            value = float((self.__state[i]["balance"]))
            if (value > 0):
                # Fill the internal state values here for coins with value > 0
                self.__readable_state[self.__state[i]["currency"]] = {
                    "Qty:": value,
                }
        return self.__readable_state

    """
    Exchange state is the external properties for the exchange block
    """
    def get_exchange_state(self):
        return self.__calls.getFees()