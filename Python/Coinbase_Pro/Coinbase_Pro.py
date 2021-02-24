import cryptofeed
from Predictor_Main import Predictor

class Coinbase_Pro:
    def __init__(self, name, user_preferences, API_KEY, API_SECRET, API_PASS):
        self.__user_preferences = user_preferences
        self.__exchange = "coinbase_pro"
        self.__name = name
        # Create the authenticated object that the prediction script can use
        # self.__calls = API(API_KEY, API_SECRET, API_PASS)

        self.__state = {
            "Value": 0,
            "24_Hr_Volume": 0,
            "P/L": 0,
        }

        # Initialize the attached script
        self.init_model()

    def get_exchange(self):
        return self.__exchange

    def get_name(self):
        return self.__name

    def exchange_command(self, command, args):
        return getattr(self, command, args)

    def get_state(self):
        # currencies = self.__calls.getAccounts()
        base_currency = self.__user_preferences["settings"]["base_currency"]
        base_currency_value = 0
        # for i in range(len(currencies)):
        #     if (currencies[i]["currency"] == base_currency):
        #         base_currency_value = currencies[i]["currency"]
        #
        # state = {
        #     "Currencies": currencies,
        #     "Base_Currency": base_currency_value,
        #
        # }
        # return state
        state = {
            "Currencies": 1,
            "Base_Currency": 23,

        }
        return state

    def init_model(self, args=None):
        if args is None:
            args = []
        self.model = Predictor(args)