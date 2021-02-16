from requests.auth import AuthBase
import time, base64, hmac, hashlib, requests, Utils, Exchange, json, LocalAccount, datetime as DT


# Create custom authentication for Exchange
class CoinbaseExchangeAuth(AuthBase):
    # Provided by CBPro: https://docs.pro.coinbase.com/#signing-a-message
    def __init__(self, api_key, secret_key, passphrase):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase

    def __call__(self, request):
        timestamp = str(time.time())
        message = ''.join([timestamp, request.method,
                           request.path_url, (request.body or '')])
        request.headers.update(get_auth_headers(timestamp, message,
                                                self.api_key,
                                                self.secret_key,
                                                self.passphrase))
        return request


def get_auth_headers(timestamp, message, api_key, secret_key, passphrase):
    message = message.encode('ascii')
    hmac_key = base64.b64decode(secret_key)
    signature = hmac.new(hmac_key, message, hashlib.sha256)
    signature_b64 = base64.b64encode(signature.digest()).decode('utf-8')
    return {
        'Content-Type': 'Application/JSON',
        'CB-ACCESS-SIGN': signature_b64,
        'CB-ACCESS-TIMESTAMP': timestamp,
        'CB-ACCESS-KEY': api_key,
        'CB-ACCESS-PASSPHRASE': passphrase
    }


class API:
    def __init__(self, API_KEY, API_SECRET, API_PASS, API_URL='https://api.pro.coinbase.com/'):
        self.__auth = CoinbaseExchangeAuth(API_KEY, API_SECRET, API_PASS)
        self.__api_url = API_URL
        self.__Utils = Utils.Utils()

    def getAccounts(self, show=False):
        output = requests.get(self.__api_url + 'accounts', auth=self.__auth)
        if show:
            self.__Utils.printJSON(output)
        return output.json()


    def getAccountInfo(self, currency, property=None, show=False):
        accounts = self.getAccounts()
        if property == None:
            for i in range(len(accounts)):
                if accounts[i]["currency"] == currency:
                    out = accounts[i]
                    if show:
                        print(out)
                    return out
        else:
            for i in range(len(accounts)):
                if accounts[i]["currency"] == currency:
                    out = accounts[i][property]
                    if show:
                        print(out)
                    return out

    """
    Example placeOrder response (this is a limit):
    {
      "status": "pending", 
      "created_at": "2021-01-10T04:39:35.96959Z", 
      "post_only": false, 
      "product_id": "BTC-USD", 
      "fill_fees": "0", 
      "settled": false, 
      "price": "15000", 
      "executed_value": "0", 
      "id": "8e102545-a103-42e0-917a-933a95ecf65b", 
      "time_in_force": "GTC", 
      "stp": "dc", 
      "filled_size": "0", 
      "type": "limit", 
      "side": "buy", 
      "size": "0.001"
    }
    """

    """
    This should be spawned entirely through the Exchange class
    """
    def placeOrder(self, order, ticker, show=False):
        output = requests.post(self.__api_url + 'orders', json=order, auth=self.__auth)

        if (str(output) == "<Response [400]>"):
            print(output)
            self.__Utils.printJSON(output)
            raise Exception("Invalid Request")

        if show:
            self.__Utils.printJSON(output)
        output = output.json()
        return output
        # try:
        #     exchangeLog = Exchange.Exchange(order["side"], order["size"], ticker, output, self, limit=order["price"])
        # except Exception as e:
        #     exchangeLog = Exchange.Exchange(order["side"], order["size"], ticker, self, output)

    def getCoinInfo(self, coinID, show=False):
        output = requests.get(self.__api_url + 'currencies/' + coinID, auth=self.__auth)
        if show:
            self.__Utils.printJSON(output)
        return output.json()

    def getOpenOrders(self, show=False):
        output = requests.get(self.__api_url + "orders", auth=self.__auth)
        if show:
            self.__Utils.printJSON(output)
        return output.json()

    def deleteOrder(self, id, show=False):
        output = requests.delete(self.__api_url + "orders/" + id, auth=self.__auth)
        if show:
            self.__Utils.printJSON(output)
        return output.json()

    """ Current maker & taker fee rates as well as your 30-day trading volume """

    def getFees(self, show=False):
        output = requests.get(self.__api_url + "fees", auth=self.__auth)
        if show:
            self.__Utils.printJSON(output)
        return output.json()

    def getPriceData(self, timeStart, timeStop, granularity, id, show=False):
        start = DT.datetime.utcfromtimestamp(timeStart).isoformat()
        stop = DT.datetime.utcfromtimestamp(timeStop).isoformat()
        query = {
            "start": start,
            "end": stop,
            "granularity": granularity
        }
        response = requests.get(self.__api_url + "products/" + id + "/candles", auth=self.__auth)
        if show:
            self.__Utils.printJSON(response)
        return response
