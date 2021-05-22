import alpaca_trade_api as tradeapi
import os

APCA_API_LIVE_URL = "https://api.alpaca.markets"
APCA_API_PAPER_URL = "https://paper-api.alpaca.markets"


class API:
    def __init__(self, API_KEY, API_SECRET, paper_trading = False):
        if (paper_trading):
            self.__api_url = APCA_API_PAPER_URL
        else:
            self.__api_url = APCA_API_LIVE_URL

        self.alp_client = tradeapi.REST(API_KEY, API_SECRET, self.__api_url, 'v2')


api = os.getenv("ALPACA_PUBLIC")
secret = os.getenv("ALPACA_PRIVATE")

if __name__ == "__main__":
    client = API(api, secret, True)
    print(client.alp_client.list_assets())