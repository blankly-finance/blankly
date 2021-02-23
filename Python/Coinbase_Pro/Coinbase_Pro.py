from Coinbase_Pro.Coinbase_Pro_API import API as API

class Coinbase_Pro:
    def __init__(self, name, user_preferences, API_KEY, API_SECRET, API_PASS):
        self.__user_preferences = user_preferences
        self.__exchange = "coinbase_pro"
        self.API_KEY = API_KEY
        self.API_SECRET = API_SECRET
        self.API_PASS = API_PASS
        self.__name = name
        # Create the authenticated object that the prediction script can use
        self.__calls = API(self.API_KEY, self.API_SECRET, self.API_PASS)

        self.__state = {
            "Value": 0,
            "24_Hr_Volume": 0,
            "P/L": 0,
        }

        # Initialize the attached script
        self.init_model("Predictor_Demo")

    def get_exchange(self):
        return self.__exchange

    def get_name(self):
        return self.__name

    def getCalls(self):
        return self.__calls

    def exchange_command(self, command, args):
        return getattr(self, command, args)

    def get_state(self):
        currencies = self.__calls.getAccounts()
        base_currency = self.__user_preferences["settings"]["base_currency"]
        base_currency_value = 0
        for i in range(len(currencies)):
            if (currencies[i]["currency"] == base_currency):
                base_currency_value = currencies[i]["currency"]

        state = {
            "Currencies": currencies,
            "Base_Currency": base_currency_value,

        }
        return state

    def init_model(self, model_name):
        return False