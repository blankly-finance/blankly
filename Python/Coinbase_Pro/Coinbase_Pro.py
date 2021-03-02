import cryptofeed, json
from Exchange import Exchange
from Predictor_Main import Predictor
from Coinbase_Pro.Coinbase_Pro_API import API


class Coinbase_Pro(Exchange):
    def __init__(self, name, user_preferences, auth):
        self.__calls = API(auth[0], auth[1], auth[2])

        initial_state = {
            "Value": 0,
            "Volume": 0
        }
        # Initialize the attached script
        self.model = Predictor("coinbase_pro", initial_state)
        Exchange.__init__(self, "coinbase_pro", name, user_preferences, self.model)
        self.get_state()

    def get_state(self):
        self.__state = self.__calls.getAccounts()
        self.__readable_state = {

        }
        for i in range(len(self.__state)):
            value = float(self.__state[i]["balance"].rstrip("0"))
            if (value > 0):
                self.__readable_state[self.__state[i]["currency"]] = self.__state[i]["balance"]
        return self.__readable_state