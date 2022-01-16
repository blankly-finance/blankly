from blankly.exchanges.auth.abc_auth import ABCAuth


class KucoinAuth(ABCAuth):
    def __init__(self, keys_file, portfolio_name):
        super().__init__(keys_file, portfolio_name, 'kucoin')
        needed_keys = ['API_KEY', 'API_SECRET', 'API_PASS']
        self.validate_credentials(needed_keys)