from blankly.exchanges.exchange import Exchange
from blankly.exchanges.interfaces.oanda.oanda_api import OandaAPI
from blankly.exchanges.auth.auth_constructor import AuthConstructor


class Oanda(Exchange):
    def __init__(self, portfolio_name=None, keys_path="keys.json", settings_path=None):
        Exchange.__init__(self, "oanda", portfolio_name, settings_path)

        # Load the auth from the keys file
        auth = AuthConstructor(keys_path, portfolio_name, 'oanda', ['PERSONAL_ACCESS_TOKEN', 'ACCOUNT_ID'])

        keys = auth.keys
        calls = OandaAPI(personal_access_token=keys['PERSONAL_ACCESS_TOKEN'],
                         account_id=keys['ACCOUNT_ID'],
                         sandbox=self.preferences["settings"]["use_sandbox"])

        # Always finish the method with this function
        super().construct_interface_and_cache(calls)

    def get_exchange_state(self):
        return self.interface.get_fees()

    def get_asset_state(self, symbol):
        return self.interface.get_account(symbol)

    def get_direct_calls(self) -> OandaAPI:
        return self.calls
