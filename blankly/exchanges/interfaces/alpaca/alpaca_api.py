from blankly.exchanges.auth.abc_auth import ABCAuth

import alpaca_trade_api
import os

APCA_API_LIVE_URL = "https://api.alpaca.markets"
APCA_API_PAPER_URL = "https://paper-api.alpaca.markets"


def create_alpaca_client(auth: ABCAuth, sandbox_mode=True):
    if sandbox_mode:
        api_url = APCA_API_PAPER_URL
    else:
        api_url = APCA_API_LIVE_URL

    return alpaca_trade_api.REST(auth.keys['API_KEY'], auth.keys['API_SECRET'], api_url, 'v2', raw_data=True)


class API:
    def __init__(self, auth: ABCAuth, paper_trading=True):
        if paper_trading:
            self.__api_url = APCA_API_PAPER_URL
        else:
            self.__api_url = APCA_API_LIVE_URL

        self.alp_client = alpaca_trade_api.REST(auth.keys['API_KEY'], auth.keys['API_SECRET'], self.__api_url, 'v2')


api = os.getenv("ALPACA_PUBLIC")
secret = os.getenv("ALPACA_PRIVATE")