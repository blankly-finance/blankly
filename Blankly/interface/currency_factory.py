from Blankly.auth.abc_auth import auth_interface
from Blankly.exchanges.Alpaca.alpaca_api_interface import AlpacaInterface
from Blankly.exchanges.Coinbase_Pro.Coinbase_Pro_API import API as Coinbase_Pro_API
from binance.client import Client
from Blankly.exchanges.Alpaca.Alpaca_API import create_alpaca_client
from Blankly.exchanges.Coinbase_Pro.Coinbase_Pro_Interface import CoinbaseProInterface
from Blankly.exchanges.Binance.Binance_Interface import BinanceInterface
import Blankly.utils.utils as utils

class InterfaceFactory:
    @staticmethod
    def create_interface(exchange_name: str, auth: auth_interface, preferences_path: str = None):
        preferences = utils.load_user_preferences(preferences_path)
        if exchange_name == 'coinbase_pro':
            if preferences["settings"]["use_sandbox"]:
                calls = Coinbase_Pro_API(auth, API_URL="https://api-public.sandbox.pro.coinbase.com/")
            else:
                # Create the authenticated object
                calls = Coinbase_Pro_API(auth)

            return CoinbaseProInterface(exchange_name, calls)

        elif exchange_name == 'binance':
            if preferences["settings"]["use_sandbox"] or preferences["settings"]["paper_trade"]:
                calls = Client(api_key=auth.API_KEY, api_secret=auth.API_SECRET,
                                      tld=preferences["settings"]["binance_tld"],
                                      testnet=True)
            else:
                calls = Client(api_key=auth.API_KEY, api_secret=auth.API_SECRET,
                                      tld=preferences["settings"]["binance_tld"])
            return BinanceInterface(exchange_name, calls)

        elif exchange_name == 'alpaca':
            calls = create_alpaca_client(auth, preferences["settings"]["use_sandbox"])
            return AlpacaInterface(calls, preferences_path)