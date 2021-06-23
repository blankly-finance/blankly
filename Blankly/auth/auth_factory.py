from Blankly.auth.Alpaca.auth import AlpacaAuth
from Blankly.auth.Binance.auth import BinanceAuth
from Blankly.auth.Coinbase.auth import CoinbaseAuth


class AuthFactory:
    @staticmethod
    def create_auth(keys_file, exchange_name, portfolio_name):
        if exchange_name == 'alpaca':
            return AlpacaAuth(keys_file, portfolio_name)
        elif exchange_name == 'binance':
            return BinanceAuth(keys_file, portfolio_name)
        elif exchange_name == 'coinbase_pro':
            return CoinbaseAuth(keys_file, portfolio_name)
        elif exchange_name == 'paper_trade':
            return None
        else:
            raise KeyError("Exchange not supported")
