from __future__ import print_function
from calc import calc as real_calc
import sys
import zerorpc
from Exchange import Exchange
from Coinbase_Pro.Coinbase_Pro import Coinbase_Pro
import Utils
import json


# A new process will be created for each total exchange. Bots can be appended to the predictor
class TradeInterface(object):
    def calc(self, text):
        """based on the input text, return the int result"""
        try:
            return real_calc(text)
        except Exception as e:
            return 0.0

    def echo(self, text):
        """echo any text """
        return text

    def init(self):
        self.__exchanges = []
        self.__utils = Utils.Utils()
        # Called from the dashboard
        try:
            with open('./Settings.json', 'r') as f:
                self.__user_preferences = json.load(f)
        # Must've been run in this folder
        except FileNotFoundError as e:
            with open('../Tradingbot/Settings.json', 'r') as f:
                self.__user_preferences = json.load(f)

    def add_exchange(self, exchange_name, exchange_type, auth):
        if exchange_type == "coinbase_pro":
            self.__exchanges.append(Coinbase_Pro(exchange_name, self.__user_preferences, auth))
            return exchange_name
        else:
            Exception("Exchange type not found")

    """ External State """
    def get_exchange_state(self, name):
        for i in range(len(self.__exchanges)):
            if (self.__exchanges[i].get_name() == name):
                return [self.__exchanges[i].get_exchange_state(), name]

    """ 
    Internal State, this has all the currencies. This is mainly used for an initial definition of which currencies
    are being used, get model state is what will matter for the reporting into these blocks
    """
    def get_portfolio_state(self, name):
        for i in range(len(self.__exchanges)):
            if (self.__exchanges[i].get_name() == name):
                return [self.__exchanges[i].get_portfolio_state(), name]

    def run_model(self, name, currency=None):
        for i in range(len(self.__exchanges)):
            if (self.__exchanges[i].get_name() == name):
                return [self.__exchanges[i].start_models(currency), name]

    def assign_model(self, exchange_name, model_name, currency, args=None):
        for i in range(len(self.__exchanges)):
            if (self.__exchanges[i].get_name() == exchange_name):
                return [self.__exchanges[i].append_model(currency, args, model_name), exchange_name]

    """
    Three indicators at the top of the GUI - JSON with only 3 keys
    """
    def update_indicators(self, name):
        for i in range(len(self.__exchanges)):
            if (self.__exchanges[i].get_name() == name):
                return self.__exchanges[i].get_indicators()



def parse_port():
    port = 4242
    try:
        port = int(sys.argv[1])
    except Exception as e:
        pass
    return '{}'.format(port)

def main():
    addr = 'tcp://127.0.0.1:' + parse_port()
    s = zerorpc.Server(TradeInterface())
    s.bind(addr)
    print('start running on {}'.format(addr))
    s.run()

if __name__ == '__main__':
    main()