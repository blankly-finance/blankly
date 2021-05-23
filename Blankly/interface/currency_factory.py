from Blankly.exchanges.Coinbase_Pro.Coinbase_Pro_API import API as Coinbase_Pro_API
from binance.client import Client

from Blankly.exchanges.Coinbase_Pro.Coinbase_Pro_Interface import CoinbaseProInterface
from Blankly.exchanges.Binance.Binance_Interface import BinanceInterface


class InterfaceFactory:
    def create_interface(self, name, preferences, auth):
        if name == 'coinbase_pro':
            if preferences["settings"]["use_sandbox"]:
                calls = Coinbase_Pro_API(auth[0], auth[1], auth[2],
                                         API_URL="https://api-public.sandbox.pro.coinbase.com/")
            else:
                # Create the authenticated object
                calls = Coinbase_Pro_API(auth[0], auth[1], auth[2])

            return CoinbaseProInterface(name, calls)

        elif name == 'binance':
            if preferences["settings"]["use_sandbox"] or preferences["settings"]["paper_trade"]:
                calls = Client(api_key=auth[0], api_secret=auth[1],
                               tld=preferences["settings"]["binance_tld"],
                               testnet=True)
            else:
                calls = Client(api_key=auth[0], api_secret=auth[1],
                               tld=preferences["settings"]["binance_tld"])
            return BinanceInterface(name, calls)

        elif name == 'alpaca':
            pass
