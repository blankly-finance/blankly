from __future__ import print_function
from calc import calc as real_calc
import sys
import zerorpc
from Coinbase_Pro.Coinbase_Pro import Coinbase_Pro
import Utils

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

    # TODO - Generalize this for any API - maybe a wrapper for each API scripts?
    def init_coinbase_pro(self):
        self.__exchange = "coinbase_pro"
        self.__utils = Utils.Utils()
        self.__exchanges = []
        return True

    def add_exchange(self, exchange_name, API_KEY, API_SECRET, API_PASS):
        self.__exchanges.append(Coinbase_Pro(exchange_name, API_KEY, API_SECRET, API_PASS))

    def API_Call(self, name, command, **kwargs):
        for i in range(len(self.__exchanges)):
            if (self.__exchanges[i].getName() == name):
                self.__exchanges[i].runCommand(command, **kwargs)

    def get_all_accounts(self):
        return str(self.__calls.getAccounts())


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