from blankly.exchanges.exchange import Exchange
from blankly.exchanges.auth.auth_constructor import AuthConstructor
from blankly.exchanges.interfaces.okx.okx_api import Client as OkxAPI, MarketAPI, AccountAPI, TradeAPI, ConvertAPI, \
    FundingAPI, PublicAPI


class Okx(Exchange):
    def __init__(self, portfolio_name=None, keys_path="keys.json", settings_path=None):
        Exchange.__init__(self, "okx", portfolio_name, settings_path)

        # Load the auth from the keys file
        auth = AuthConstructor(keys_path, portfolio_name, 'okx', ['API_KEY', 'API_SECRET', 'API_PASS', 'sandbox'])
        keys = auth.keys

        sandbox = super().evaluate_sandbox(auth)

        # if self.preferences["settings"]["use_sandbox"]:
        calls = {
            'market': MarketAPI(api_key=keys['API_KEY'], api_secret_key=keys['API_SECRET'],passphrase=keys['API_PASS'],
                                sandbox=sandbox),
            'account': AccountAPI(api_key=keys['API_KEY'], api_secret_key=keys['API_SECRET'], passphrase=keys['API_PASS'],
                                  sandbox=sandbox),
            'trade': TradeAPI(api_key=keys['API_KEY'], api_secret_key=keys['API_SECRET'], passphrase=keys['API_PASS'],
                              sandbox=sandbox),
            'convert': ConvertAPI(api_key=keys['API_KEY'], api_secret_key=keys['API_SECRET'], passphrase=keys['API_PASS'],
                                  sandbox=sandbox),
            'funding': FundingAPI(api_key=keys['API_KEY'], api_secret_key=keys['API_SECRET'], passphrase=keys['API_PASS'],
                                  sandbox=sandbox),
            'public': PublicAPI(api_key=keys['API_KEY'], api_secret_key=keys['API_SECRET'], passphrase=keys['API_PASS'],
                                sandbox=sandbox)
        }

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
        return self.interface.get_products()

    def get_direct_calls(self) -> dict:
        return self.calls
