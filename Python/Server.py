from __future__ import print_function
from calc import calc as real_calc
import sys
import zerorpc
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
        """echo any text"""
        return text

    def init_general(self):
        with open('../Settings.json', 'r') as f:
            self.__user_preferences = json.load(f)

    # TODO - Generalize this for any API - maybe a wrapper for each API scripts?
    def init_coinbase_pro(self):
        self.__exchange = "coinbase_pro"
        self.__utils = Utils.Utils()
        self.__exchanges = []
        # self.init_general()
        return True

    def add_exchange(self, exchange_name, API_KEY, API_SECRET, API_PASS):
        # Needs to be generalized
        # TODO make this load the actual preferences
        self.__user_preferences = None
        self.__exchanges.append(Coinbase_Pro(exchange_name, self.__user_preferences, API_KEY, API_SECRET, API_PASS))
        return True


    def get_exchange_state(self, name, written_name):
        for i in range(len(self.__exchanges)):
            if (self.__exchanges[i].get_name() == name):
                return self.__exchanges[i].get_state()


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