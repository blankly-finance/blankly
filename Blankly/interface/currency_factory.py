from Blankly.exchanges.Alpaca.alpaca_api_interface import AlpacaInterface
from Blankly.exchanges.Coinbase_Pro.Coinbase_Pro_API import API as Coinbase_Pro_API
from binance.client import Client
from Blankly.exchanges.Alpaca.Alpaca_API import API as Alpaca_API
from Blankly.exchanges.Coinbase_Pro.Coinbase_Pro_Interface import CoinbaseProInterface
from Blankly.exchanges.Binance.Binance_Interface import BinanceInterface
from Blankly.auth.auth_factory import AuthFactory

class InterfaceFactory:

    @staticmethod
    def create_interface(exchange_name: str, preferences, auth):
        if exchange_name == 'coinbase_pro':
            if preferences["settings"]["use_sandbox"]:
                calls = Coinbase_Pro_API(auth[0], auth[1], auth[2],
                                                API_URL="https://api-public.sandbox.pro.coinbase.com/")
            else:
                # Create the authenticated object
                calls = Coinbase_Pro_API(auth[0], auth[1], auth[2])

            return CoinbaseProInterface(exchange_name, calls)

        elif exchange_name == 'binance':
            if preferences["settings"]["use_sandbox"] or preferences["settings"]["paper_trade"]:
                calls = Client(api_key=auth[0], api_secret=auth[1],
                                      tld=preferences["settings"]["binance_tld"],
                                      testnet=True)
            else:
                calls = Client(api_key=auth[0], api_secret=auth[1],
                                      tld=preferences["settings"]["binance_tld"])
            return BinanceInterface(exchange_name, calls)

        elif exchange_name == 'alpaca':
            # TODO: Fix the hardcoded true
            calls = Alpaca_API(auth, True)
            return AlpacaInterface(calls)