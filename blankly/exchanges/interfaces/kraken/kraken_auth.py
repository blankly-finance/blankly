from blankly.exchanges.auth.abc_auth import ABCAuth


class KrakenAuth(ABCAuth):
    def __init__(self, keys_file, portfolio_name):
        super().__init__(keys_file, portfolio_name, 'kraken')
        needed_keys = ['API_KEY', 'API_SECRET']
        self.validate_credentials(needed_keys)
