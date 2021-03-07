import cryptofeed, json
from Exchange import Exchange
from Predictor_Main import Predictor
from Coinbase_Pro.Coinbase_Pro_API import API
from API_Interface import APIInterface


class Coinbase_Pro(Exchange):
    def __init__(self, name, user_preferences, auth):
        self.__calls = API(auth[0], auth[1], auth[2])

        Exchange.__init__(self, "coinbase_pro", name, user_preferences)
        # Create the authenticated object
        self.__APIInterface = APIInterface("coinbase_pro", self.__calls)
        self.get_state()

        # Create the model container
        self.models = {}

    def get_state(self):
        self.__state = self.__calls.getPortfolio()
        return self.__state

    """
    Portfolio state is the internal properties for the exchange block
    """
    def get_portfolio_state(self, only_active=True):
        self.get_state()
        self.__readable_state = {}
        unused = {}
        for i in range(len(self.__state)):
            value = float((self.__state[i]["balance"]))
            if value > 0:
                self.__readable_state[self.__state[i]["currency"]] = {
                    "Qty:": value,
                }
                currency = (self.__state[i]["currency"])
                # There can be no currency state until a model is added to the currency
                try:
                    self.__readable_state[self.__state[i]["currency"]] = {**self.__readable_state[self.__state[i]["currency"]], **self.get_model_state(currency)}
                except KeyError as e:
                    pass
            else:
                unused[self.__state[i]["currency"]] = {
                    "Qty:": 0,
                }

        if only_active:
            return self.__readable_state
        else:
            return {**self.__readable_state, **unused}

    """
    State for just this new currency
    """
    def get_currency_state(self, currency):
        return self.get_portfolio_state(False)[currency]

    """
    Exchange state is the external properties for the exchange block
    """
    def get_exchange_state(self):
        return self.__calls.getFees()

    """
    Append the models to the exchange, these can be run
    """
    def append_model(self, coin, args=None, id=None):
        added_model = Predictor("coinbase_pro", self.get_currency_state(coin), self.__APIInterface)
        self.models[coin] = {
            "model": added_model,
            "args": args
        }

    """
    Start all models or a specific one after appending it to to the exchange
    """
    def start_models(self, coin=None):
        if coin is not None:
            # Run a specific model with the args
            if not self.models[coin]["model"].is_running():
                self.models[coin]["model"].run(self.models[coin]["args"])
            return "Started model attached to: " + coin
        else:
            for coin_iterator in self.models:
                # Start all models
                if not self.models[coin_iterator]["model"].is_running():
                    self.models[coin_iterator]["model"].run(self.models[coin_iterator]["args"])
                else:
                    print("Ignoring the model on " + coin_iterator)
            return "Started all models"

    def get_model(self, coin):
        return self.models[coin]["model"]

    def get_model_state(self, coin):
        return (self.get_model(coin)).get_state()
