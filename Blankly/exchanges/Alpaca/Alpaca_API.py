from Blankly.auth.Alpaca.auth import alpaca_auth

import alpaca_trade_api
import os

APCA_API_LIVE_URL = "https://api.alpaca.markets"
APCA_API_PAPER_URL = "https://paper-api.alpaca.markets"

def create_alpaca_client(auth: alpaca_auth, paper_trading=True):
    if paper_trading:
        api_url = APCA_API_PAPER_URL
    else:
        api_url = APCA_API_LIVE_URL

    return alpaca_trade_api.REST(auth.API_KEY, auth.API_SECRET, api_url, 'v2', raw_data=True)

class API:
    def __init__(self, auth: alpaca_auth, paper_trading=True):
        if paper_trading:
            self.__api_url = APCA_API_PAPER_URL
        else:
            self.__api_url = APCA_API_LIVE_URL

        self.alp_client = alpaca_trade_api.REST(auth.API_KEY, auth.API_SECRET, self.__api_url, 'v2')


api = os.getenv("ALPACA_PUBLIC")
secret = os.getenv("ALPACA_PRIVATE")

if __name__ == "__main__":
    client = API(api, secret, True)
    print(client.alp_client.list_assets())
