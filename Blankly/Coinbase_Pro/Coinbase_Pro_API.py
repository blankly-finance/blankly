"""
    Calls to the Coinbase Pro API.
    Copyright (C) 2021  Emerson Dove

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from requests.auth import AuthBase
import time, base64, hmac, hashlib, requests, Blankly.Utils, datetime as DT, cbpro


class API:
    def __init__(self, API_KEY, API_SECRET, API_PASS, API_URL='https://api.pro.coinbase.com/'):
        self.auth_client = cbpro.AuthenticatedClient(API_KEY, API_SECRET, API_PASS)

    """
    Public Client Calls
    """
    def get_products(self):
        return self.auth_client.get_products()

    def get_product_order_book(self, product_id, level=1):
        return self.auth_client.get_product_order_book(product_id, level=level)

    def get_product_trades(self, product_id):
        return self.auth_client.get_product_trades(product_id=product_id)

    def get_product_historic_rates(self, product_id, granularity=3000):
        return self.auth_client.get_product_historic_rates(product_id=product_id, granularity=granularity)

    def get_product_24hr_stats(self, product_id):
        return self.auth_client.get_product_24hr_stats(product_id=product_id)

    def get_currencies(self):
        return self.auth_client.get_currencies()

    def get_time(self):
        return self.auth_client.get_time()

    """
    Private API Calls
    """

    def get_accounts(self):
        return self.auth_client.get_accounts()

    def get_account(self, account_id):
        return self.auth_client.get_account(account_id=account_id)

    def get_account_history(self, account_id):
        return self.auth_client.get_account_history(account_id=account_id)

    def get_account_holds(self, account_id):
        return self.auth_client.get_account_holds(account_id=account_id)

    """
    Buy & sell
    """
    def place_limit_order(self, product_id, side, price, size):
        return self.auth_client.place_limit_order(product_id, side, price, size)

    def place_market_order(self, product_id, side, funds):
        return self.auth_client.place_market_order(product_id, side, funds)

    def place_stop_order(self, product_id, stop_type, price, size):
        return self.auth_client.place_stop_order(product_id, stop_type, price, size)

    def cancel_order(self, order_id):
        return self.auth_client.cancel_order(order_id)

    def get_orders(self):
        return self.auth_client.get_orders()

    def get_order(self, order_id):
        return self.auth_client.get_order(order_id)

    def get_fills(self, order_id=None, product_id=None):
        return self.auth_client.get_fills(order_id, product_id)



# # Create custom authentication for Exchange
# class CoinbaseExchangeAuth(AuthBase):
#     # Provided by CBPro: https://docs.pro.coinbase.com/#signing-a-message
#     def __init__(self, api_key, secret_key, passphrase):
#         self.api_key = api_key
#         self.secret_key = secret_key
#         self.passphrase = passphrase
#
#     def __call__(self, request):
#         timestamp = str(time.time())
#         message = ''.join([timestamp, request.method,
#                            request.path_url, (request.body or '')])
#         request.headers.update(get_auth_headers(timestamp, message,
#                                                 self.api_key,
#                                                 self.secret_key,
#                                                 self.passphrase))
#         return request
#
#
# def get_auth_headers(timestamp, message, api_key, secret_key, passphrase):
#     message = message.encode('ascii')
#     hmac_key = base64.b64decode(secret_key)
#     signature = hmac.new(hmac_key, message, hashlib.sha256)
#     signature_b64 = base64.b64encode(signature.digest()).decode('utf-8')
#     return {
#         'Content-Type': 'Application/JSON',
#         'CB-ACCESS-SIGN': signature_b64,
#         'CB-ACCESS-TIMESTAMP': timestamp,
#         'CB-ACCESS-KEY': api_key,
#         'CB-ACCESS-PASSPHRASE': passphrase
#     }
#
#
# class API:
#     def __init__(self, API_KEY, API_SECRET, API_PASS, API_URL='https://api.pro.coinbase.com/'):
#         self.__auth = CoinbaseExchangeAuth(API_KEY, API_SECRET, API_PASS)
#         self.__api_url = API_URL
#         self.__Utils = Blankly.Utils.Utils()
#
#     def get_portfolio(self, currency=None, show=False):
#         output = requests.get(self.__api_url + 'accounts', auth=self.__auth).json()
#         if show:
#             self.__Utils.printJSON(output)
#
#         if currency is not None:
#             for i in range(len(output)):
#                 if output[i]["currency"] == currency:
#                     out = output[i]
#                     if show:
#                         print(out)
#                     return out
#             raise Exception("Currency not found")
#         return output
#
#     @DeprecationWarning
#     def getAccountInfo(self, currency, property=None, show=False):
#         accounts = self.get_portfolio()
#         if property == None:
#             for i in range(len(accounts)):
#                 if accounts[i]["currency"] == currency:
#                     out = accounts[i]
#                     if show:
#                         print(out)
#                     return out
#         else:
#             for i in range(len(accounts)):
#                 if accounts[i]["currency"] == currency:
#                     out = accounts[i][property]
#                     if show:
#                         print(out)
#                     return out
#
#     """
#     Example placeOrder response (this is a limit):
#     {
#       "status": "pending",
#       "created_at": "2021-01-10T04:39:35.96959Z",
#       "post_only": false,
#       "product_id": "BTC-USD",
#       "fill_fees": "0",
#       "settled": false,
#       "price": "15000",
#       "executed_value": "0",
#       "id": "8e102545-a103-42e0-917a-933a95ecf65b",
#       "time_in_force": "GTC",
#       "stp": "dc",
#       "filled_size": "0",
#       "type": "limit",
#       "side": "buy",
#       "size": "0.001"
#     }
#     """
#
#     """
#     This should be spawned entirely through the Exchange class
#     """
#
#     def placeOrder(self, order, show=False):
#         output = requests.post(self.__api_url + 'orders', json=order, auth=self.__auth)
#
#         if (str(output) == "<Response [400]>"):
#             print(output)
#             self.__Utils.printJSON(output)
#             raise Exception("Invalid Request")
#
#         if show:
#             self.__Utils.printJSON(output)
#         output = output.json()
#         return output
#         # try:
#         #     exchangeLog = Exchange.Exchange(order["side"], order["size"], ticker, output, self, limit=order["price"])
#         # except Exception as e:
#         #     exchangeLog = Exchange.Exchange(order["side"], order["size"], ticker, self, output)
#
#     def getCoinInfo(self, coinID, show=False):
#         output = requests.get(self.__api_url + 'currencies/' + coinID, auth=self.__auth)
#         if show:
#             self.__Utils.printJSON(output)
#         return output.json()
#
#     def getOpenOrders(self, show=False):
#         output = requests.get(self.__api_url + "orders", auth=self.__auth)
#         if show:
#             self.__Utils.printJSON(output)
#         return output.json()
#
#     def deleteOrder(self, id, show=False):
#         output = requests.delete(self.__api_url + "orders/" + id, auth=self.__auth)
#         if show:
#             self.__Utils.printJSON(output)
#         return output.json()
#
#     """ Current maker & taker fee rates as well as your 30-day trading volume """
#
#     def getFees(self, show=False):
#         output = requests.get(self.__api_url + "fees", auth=self.__auth)
#         if show:
#             self.__Utils.printJSON(output)
#         return output.json()
#
#     def getPriceData(self, timeStart, timeStop, granularity, id, show=False):
#         start = DT.datetime.utcfromtimestamp(timeStart).isoformat()
#         stop = DT.datetime.utcfromtimestamp(timeStop).isoformat()
#         query = {
#             "start": start,
#             "end": stop,
#             "granularity": granularity
#         }
#         response = requests.get(self.__api_url + "products/" + id + "/candles", auth=self.__auth)
#         if show:
#             self.__Utils.printJSON(response)
#         return response
#
#     def getPortfolios(self, show=False):
#         output = requests.get(self.__api_url + "profiles", auth=self.__auth)
#         if show:
#             self.__Utils.printJSON(output)
#         return output.json()
#
#     def getProductData(self, product_id, show=False):
#         output = requests.get(self.__api_url + "products/" + product_id)
#         if show:
#             self.__Utils.printJSON(output)
#         return output.json()
#
#     def getProductOrderBook(self, product_id, show=False):
#         output = requests.get(self.__api_url + "products/" + product_id + "/book")
#         if show:
#             self.__Utils.printJSON(output)
#         return output.json()
#
#     def getTrades(self, product_id, show=False):
#         output = requests.get(self.__api_url + "products/" + product_id + "/trades")
#         if show:
#             self.__Utils.printJSON(output)
#         return output.json()
#
#     def getCurrencies(self, id=None, show=False):
#         if id == None:
#             output = requests.get(self.__api_url + "currencies")
#         else:
#             output = requests.get(self.__api_url + "currencies/" + id)
#         if show:
#             self.__Utils.printJSON(output)
#         return output.json()
#
#     def getTime(self, show=False):
#         output = requests.get(self.__api_url + "time")
#         if show:
#             self.__Utils.printJSON(output)
#         return output.json()
