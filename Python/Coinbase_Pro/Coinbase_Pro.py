import cryptofeed, json
from Exchange import Exchange
from Predictor_Main import Predictor


class Coinbase_Pro(Exchange):
    def __init__(self, name, user_preferences, auth):
        # self.__calls = API(API_KEY, API_SECRET, API_PASS)

        initial_state = {
            "Value": 0,
            "Volume": 0
        }
        # Initialize the attached script
        self.model = Predictor("coinbase_pro", initial_state)
        Exchange.__init__(self, "coinbase_pro", name, user_preferences,self.model)
