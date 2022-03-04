from blankly.exchanges.exchange import Exchange
from blankly.exchanges.auth.auth_constructor import AuthConstructor
from blankly.exchanges.interfaces.okex.okex_api import API as OkexAPI


class Kucoin(Exchange):
    def __init__(self, portfolio_name=None, keys_path="keys.json", settings_path=None):
        Exchange.__init__(self, "okex", portfolio_name, settings_path)

        # Load the auth from the keys file
        auth = AuthConstructor(keys_path, portfolio_name, 'okex', ['API_KEY', 'API_SECRET', 'API_PASS'])
        keys = auth.keys

        # try:
        #     from okex import client as OkexAPI
        # except ImportError:
        #     raise ImportError("Please \"pip install okex-api\" to use kucoin with blankly.")

        calls = OkexAPI(api_key=keys['API_KEY'],
                        api_secret=keys['API_SECRET'],
                        api_pass=keys['API_PASS'])

        # OkexAPI(api_key=auth.keys['API_KEY'],
        #             api_secret=auth.keys['API_SECRET'],
        #             api_pass=auth.keys['API_PASS'])

        # Always finish the method with this function
        super().construct_interface_and_cache(calls)

    """
    Builds information about the asset on this exchange by making particular API calls
    """

    def get_asset_state(self, symbol):
        """
        This determines the internal properties of the exchange block.
        Should be implemented per-class because it requires different types of interaction with each exchange.
        """
        # TODO Populate this with useful information
        return self.interface.get_account(symbol)

    def get_exchange_state(self):
        """
        Exchange state is the external properties for the exchange block
        """
        # TODO Populate this with useful information
        return self.interface.get_fees()

    def get_direct_calls(self) -> dict:
        return self.calls
