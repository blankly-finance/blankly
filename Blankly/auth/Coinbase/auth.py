from Blankly.auth.abc_auth import AuthInterface
import warnings


class CoinbaseAuth(AuthInterface):
    def __init__(self, keys_file, portfolio_name):
        super().__init__(keys_file, portfolio_name, 'coinbase')
        self.API_KEY = None
        self.API_SECRET = None
        self.API_PASS = None

        self.validate_credentials()

    def validate_credentials(self):
        """
        Validate that exchange specific credentials are present
        """
        try:
            self.API_KEY = self.raw_cred.pop('API_KEY')
            self.API_SECRET = self.raw_cred.pop('API_SECRET')
            self.API_PASS = self.raw_cred.pop('API_PASS')
        except KeyError as e:
            print(f"One of 'API_KEY' or 'API_SECRET' or 'API_PASS' not defined for "
                  f"Exchange: {self.exchange} Portfolio: {self.portfolio_name}")
            raise KeyError(e)

        if len(self.raw_cred) > 0:
            warnings.warn(f"Additional keys for Exchange: {self.exchange} Portfolio: {self.portfolio_name} will be"
                          f" ignored.")



