from blankly.exchanges.interfaces.oanda.oanda_auth import OandaAuth

class OandaAPI:
    API_URL = 'https://api-fxtrade.oanda.com'
    API_PRACTICE_URL = 'https://api-fxpractice.oanda.com'

    def __init__(self, auth: OandaAuth, sandbox: bool = False):
        self.api_key = auth.keys['API_KEY']
        self.secret_key = auth.keys['API_SECRET']

        if not sandbox:
            self.__api_url = self.API_URL
        else:
            self.__api_url = self.API_PRACTICE_URL
