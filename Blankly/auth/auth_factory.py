from Blankly.auth.Alpaca.auth import alpaca_auth
from Blankly.auth.Binance.auth import binance_auth
from Blankly.auth.Coinbase.auth import coinbase_auth


class AuthFactory:
    @staticmethod
    def create_auth(self, keys_file, exchange_name, portfolio_name):
        if exchange_name == 'alpaca':
            return alpaca_auth(keys_file, portfolio_name)
        elif exchange_name == 'binance':
            return binance_auth(keys_file, portfolio_name)
        elif exchange_name == 'coinbase_pro':
            return coinbase_auth(keys_file, portfolio_name)
        else:
            raise KeyError("Exchange not supported")
