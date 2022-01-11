from blankly.exchanges.exchange import Exchange

class Kucoin(Exchange):
    def __init__(self, portfolio_name=None, keys_path="keys.json", settings_path=None):
        Exchange.__init__(self, "kucoin", portfolio_name, keys_path, settings_path)

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

    def get_direct_calls(self):
        return self.calls

