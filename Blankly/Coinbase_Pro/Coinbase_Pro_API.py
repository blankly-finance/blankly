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
import time, base64, hmac, hashlib, requests, Blankly.Utils, datetime as DT, cbpro, warnings


class API:
    def __init__(self, API_KEY, API_SECRET, API_PASS, API_URL='https://api.pro.coinbase.com/'):
        self.auth_client = cbpro.AuthenticatedClient(API_KEY, API_SECRET, API_PASS, API_URL)

    """
    Public Client Calls
    """
    def get_products(self):
        """
            Returns:
            list: Info about all currency pairs. Example::
                [
                    {
                        "id": "BTC-USD",
                        "display_name": "BTC/USD",
                        "base_currency": "BTC",
                        "quote_currency": "USD",
                        "base_min_size": "0.01",
                        "base_max_size": "10000.00",
                        "quote_increment": "0.01"
                    }
                ]
        """
        return self.auth_client.get_products()

    def get_product_order_book(self, product_id, level=1):
        """
            Returns:
            dict: Order book. Example for level 1::
                {
                    "sequence": "3",
                    "bids": [
                        [ price, size, num-orders ],
                    ],
                    "asks": [
                        [ price, size, num-orders ],
                    ]
                }

        """
        if level == 3:
            warnings.warn("Abuse of polling at level 3 can result in a block. Consider using the websocket.")

        return self.auth_client.get_product_order_book(product_id, level=level)

    """ PAGINATED """
    def get_product_trades(self, product_id, before='', after='', limit=None, result=None):
        """
            Returns:
             list: Latest trades. Example::
                 [{
                     "time": "2014-11-07T22:19:28.578544Z",
                     "trade_id": 74,
                     "price": "10.00000000",
                     "size": "0.01000000",
                     "side": "buy"
                 }, {
                     "time": "2014-11-07T01:08:43.642366Z",
                     "trade_id": 73,
                     "price": "100.00000000",
                     "size": "0.01000000",
                     "side": "sell"
         }]
        """
        return self.auth_client.get_product_trades(product_id=product_id, before=before, after=after, limit=limit, result=result)

    def get_product_historic_rates(self, product_id, start=None, end=None, granularity=None):
        """
            Returns:
            list: Historic candle data. Example:
                [
                    [ time, low, high, open, close, volume ],
                    [ 1415398768, 0.32, 4.2, 0.35, 4.2, 12.3 ],
                    ...
                ]
        """
        return self.auth_client.get_product_historic_rates(product_id, start, end, granularity)

    def get_product_24hr_stats(self, product_id):
        """
            Returns:
            dict: 24 hour stats. Volume is in base currency units.
                Open, high, low are in quote currency units. Example::
                    {
                        "open": "34.19000000",
                        "high": "95.70000000",
                        "low": "7.06000000",
                        "volume": "2.41000000"
                    }
        """
        return self.auth_client.get_product_24hr_stats(product_id=product_id)

    def get_currencies(self):
        """
            Returns:
            list: List of currencies. Example::
                [{
                    "id": "BTC",
                    "name": "Bitcoin",
                    "min_size": "0.00000001"
                }, {
                    "id": "USD",
                    "name": "United States Dollar",
                    "min_size": "0.01000000"
                }]
        """
        return self.auth_client.get_currencies()

    def get_time(self):
        """
            Returns:
            dict: Server time in ISO and epoch format (decimal seconds
                since Unix epoch). Example::
                    {
                        "iso": "2015-01-07T23:47:25.201Z",
                        "epoch": 1420674445.201
                    }
        """
        return self.auth_client.get_time()

    """
    Private API Calls
    """

    def get_accounts(self):
        """
            Returns:
            dict: Account information. Example::
                {
                    "id": "a1b2c3d4",
                    "balance": "1.100",
                    "holds": "0.100",
                    "available": "1.00",
                    "currency": "USD"
                }
        """
        return self.auth_client.get_accounts()

    def get_account(self, account_id):
        """
            Returns:
            dict: Account information. Example::
                {
                    "id": "a1b2c3d4",
                    "balance": "1.100",
                    "holds": "0.100",
                    "available": "1.00",
                    "currency": "USD"
                }
        """
        return self.auth_client.get_account(account_id=account_id)

    """ PAGINATED """
    def get_account_history(self, account_id):
        """
            Returns:
            list: History information for the account. Example::
                [
                    {
                        "id": "100",
                        "created_at": "2014-11-07T08:19:27.028459Z",
                        "amount": "0.001",
                        "balance": "239.669",
                        "type": "fee",
                        "details": {
                            "order_id": "d50ec984-77a8-460a-b958-66f114b0de9b",
                            "trade_id": "74",
                            "product_id": "BTC-USD"
                        }
                    },
                    {
                        ...
                    }
                ]
                Note that the details can change depending on what happened at that point.
        """
        return self.auth_client.get_account_history(account_id=account_id)

    """ PAGINATED """
    def get_account_holds(self, account_id):
        """
            Returns:
            generator(list): Hold information for the account. Example::
                [
                    {
                        "id": "82dcd140-c3c7-4507-8de4-2c529cd1a28f",
                        "account_id": "e0b3f39a-183d-453e-b754-0c13e5bab0b3",
                        "created_at": "2014-11-06T10:34:47.123456Z",
                        "updated_at": "2014-11-06T10:40:47.123456Z",
                        "amount": "4.23",
                        "type": "order",
                        "ref": "0a205de4-dd35-4370-a285-fe8fc375a273",
                    },
                    {
                    ...
                    }
                ]
        """
        return self.auth_client.get_account_holds(account_id=account_id)

    """
    Buy & sell
    """
    def place_limit_order(self, product_id, side, price, size):
        """
            Returns:
            dict: Order details. Example::
            {
                "id": "d0c5340b-6d6c-49d9-b567-48c4bfca13d2",
                "price": "0.10000000",
                "size": "0.01000000",
                "product_id": "BTC-USD",
                "side": "buy",
                "stp": "dc",
                "type": "limit",
                "time_in_force": "GTC",
                "post_only": false,
                "created_at": "2016-12-08T20:02:28.53864Z",
                "fill_fees": "0.0000000000000000",
                "filled_size": "0.00000000",
                "executed_value": "0.0000000000000000",
                "status": "pending",
                "settled": false
            }
        """
        return self.auth_client.place_limit_order(product_id, side, price, size)

    def place_market_order(self, product_id, side, funds):
        """
            Returns:
            dict: Order details.
            Coinbase Pro Example:
            {
                "id": "d0c5340b-6d6c-49d9-b567-48c4bfca13d2",
                "price": "0.10000000",
                "size": "0.01000000",
                "product_id": "BTC-USD",
                "side": "buy",
                "stp": "dc",
                "type": "limit",
                "time_in_force": "GTC",
                "post_only": false,
                "created_at": "2016-12-08T20:02:28.53864Z",
                "fill_fees": "0.0000000000000000",
                "filled_size": "0.00000000",
                "executed_value": "0.0000000000000000",
                "status": "pending",
                "settled": false
            }
        """
        return self.auth_client.place_market_order(product_id, side, funds)

    def place_stop_order(self, product_id, stop_type, price, size):
        """
            Returns:
            dict: Order details.
            Coinbase Pro Example:
            {
                "id": "d0c5340b-6d6c-49d9-b567-48c4bfca13d2",
                "price": "0.10000000",
                "size": "0.01000000",
                "product_id": "BTC-USD",
                "side": "buy",
                "stp": "dc",
                "type": "limit",
                "time_in_force": "GTC",
                "post_only": false,
                "created_at": "2016-12-08T20:02:28.53864Z",
                "fill_fees": "0.0000000000000000",
                "filled_size": "0.00000000",
                "executed_value": "0.0000000000000000",
                "status": "pending",
                "settled": false
            }
        """
        return self.auth_client.place_stop_order(product_id, stop_type, price, size)



    def cancel_order(self, order_id):
        """
            Returns:
            list: Containing the order_id of cancelled order. Example::
                [ "c5ab5eae-76be-480e-8961-00792dc7e138" ]
        """
        return self.auth_client.cancel_order(order_id)

    """ PAGINATED """
    def get_orders(self):
        """
            Returns:
            list: Containing information on orders. Example::
                [
                    {
                        "id": "d0c5340b-6d6c-49d9-b567-48c4bfca13d2",
                        "price": "0.10000000",
                        "size": "0.01000000",
                        "product_id": "BTC-USD",
                        "side": "buy",
                        "stp": "dc",
                        "type": "limit",
                        "time_in_force": "GTC",
                        "post_only": false,
                        "created_at": "2016-12-08T20:02:28.53864Z",
                        "fill_fees": "0.0000000000000000",
                        "filled_size": "0.00000000",
                        "executed_value": "0.0000000000000000",
                        "status": "open",
                        "settled": false
                    },
                    {
                        ...
                    }
                ]
        """
        return self.auth_client.get_orders()

    def get_order(self, order_id):
        """
            Returns:
            dict: Containing information on order. Example::
                {
                    "created_at": "2017-06-18T00:27:42.920136Z",
                    "executed_value": "0.0000000000000000",
                    "fill_fees": "0.0000000000000000",
                    "filled_size": "0.00000000",
                    "id": "9456f388-67a9-4316-bad1-330c5353804f",
                    "post_only": true,
                    "price": "1.00000000",
                    "product_id": "BTC-USD",
                    "settled": false,
                    "side": "buy",
                    "size": "1.00000000",
                    "status": "pending",
                    "stp": "dc",
                    "time_in_force": "GTC",
                    "type": "limit"
                }
        """
        return self.auth_client.get_order(order_id)

    """ PAGINATED """
    def get_fills(self, order_id=None, product_id=None):
        """
            Returns:
            list: Containing information on fills. Example::
                [
                    {
                        "trade_id": 74,
                        "product_id": "BTC-USD",
                        "price": "10.00",
                        "size": "0.01",
                        "order_id": "d50ec984-77a8-460a-b958-66f114b0de9b",
                        "created_at": "2014-11-07T22:19:28.578544Z",
                        "liquidity": "T",
                        "fee": "0.00025",
                        "settled": true,
                        "side": "buy"
                    },
                    {
                        ...
                    }
                ]
        """
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
