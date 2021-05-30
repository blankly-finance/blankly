from Blankly.auth.abc_auth import auth_interface
import warnings

class binance_auth(auth_interface):
    def __init__(self, keys_file, portfolio_name):
        super.__init__(keys_file, portfolio_name, 'binance')
        self.API_KEY = None
        self.API_SECRET = None
        self.validate_credentials()

    def validate_credentials(self):
        """
        Validate that exchange specific credentials are present
        """
        try:
            self.API_KEY = self.raw_cred.pop('API_KEY')
            self.API_SECRET = self.raw_cred.pop('API_SECRET')
        except KeyError as e:
            print(f"One of 'API_KEY' or 'API_SECRET' not defined for Exchange: {self.__exchange} Portfolio: {self.__portfolio_name}")
            raise KeyError(e)

        if len(self.raw_cred) > 0:
            warnings.warn(f"Additional configs for Exchange: {self.__exchange} Portfolio: {self.__portfolio_name} being ignored")



