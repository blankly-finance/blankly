from __future__ import print_function
from calc import calc as real_calc
import sys
import zerorpc
from CoinbaseProApiCalls import PrivateApiCalls
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
    def init_coinbase_pro(self, API_KEY, API_SECRET, API_PASS):
        self.__exchange = "coinbase_pro"
        self.__utils = Utils.Utils()
        self.__calls = PrivateApiCalls(API_KEY, API_SECRET, API_PASS)
        return str(self.__calls.getAccounts())

    def get_account_info(self, id):
        return str(self.__calls.getAccountInfo(id))

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