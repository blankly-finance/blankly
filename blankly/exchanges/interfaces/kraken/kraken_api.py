import hmac
import hashlib
from multiprocessing.sharedctypes import Value
import time
import urllib
import base64
import binascii
import requests
#from . import version
import requests


class API:
    
    def __init__(self, api_key, api_secret, API_URL='https://api.kraken.com', timeout=30):
        self.__api_url = API_URL
        self.session = requests.Session()

        self._api_key = api_key
        self._api_secret = api_secret
        self.timeout = [timeout]
        self.proxy = {}
        self.version = "0"

        
        
        # Short info about API client
        self.headers = {
            "User-Agent": "Blankly-finance",
            "Version": self.version
        }

        # List of all supported Request Strings.
        self.supported_requests = {
            "private": [
                "Balance", "TradeBalance", "OpenOrders", "ClosedOrders", "QueryOrders", "TradesHistory",
                "QueryTrades", "OpenPositions", "Ledgers", "QueryLedgers", "TradeVolume", "AddOrder",
                "CancelOrder", "DepositMethods", "DepositAddress", "DepositStatus", "WithdrawInfo", "Withdraw",
                "WithdrawStatus", "WithdrawCancel"
            ],
            "public": [
                "Time", "Assets", "AssetPairs", "Ticker", "OHLC", "Depth", "Trades", "Spread"
            ]
        }

    def public(self, request, parameters=None):
        """
        Creates a public API call. It does not require public and private keys to be set.
        :param str  request:    One of ``Time``, ``Assets``, ``AssetPairs``, ``Ticker``, ``OHLC``, ``Depth``, \
                                ``Trades`` and ``Spread``.
        :param dict parameters: Additional parameters for each request. See Kraken documentation for more information.
        :returns:               JSON object representing Kraken API response.
        :raises:                ``ValueError``, if request string is not valid. ``ConnectionError`` and \
                                ``ConnectionTimeout`` on connection problem.
        
        """

        parameters = parameters if parameters else {}

        # Raise error on unsupported input
        if request not in self.supported_requests["public"]:
            raise ValueError("Request string % is not supported by public API calls.".format(request))

        # Path to the requested api call
        path = self.__api_url + '/' + self.version + '/public/' + request

        # Connect to API server
        try:
            response = requests.post(
                path,
                data=parameters,
                headers=self.headers,
                timeout=self.timeout[0],
                proxies=self.proxy
            )
        except requests.exceptions.ConnectionError:
            raise ConnectionError()
        except requests.exceptions.Timeout:
            raise ConnectionTimeout()
        except requests.exceptions.TooManyRedirects:
            raise ConnectionError()

        if response.status_code != 200:
            raise ConnectionError()
        else:
            
            err_len = response.json()["error"]
            if len(err_len) > 0:
                raise ValueError(f"kraken API error: {err_len}")
            else:
                return response.json()["result"]

    def time(self)-> dict:
        """
        {  
            "error":[  
            
            ],
            "result":{  
                "rfc1123":"Wed, 10 May 17 10:32:24 +0000",
                "unixtime":1494412344
            }
        }

        """

        return self.public("Time")

    def assets(self, assets="") -> dict:
        """
        {  
            "result":{  
                "XMLN":{  
                    "altname":"MLN",
                    "decimals":10,
                    "display_decimals":5,
                    "aclass":"currency"
                },
                
                ...
            }
        }
        """

        # According to documentation, info and aclass have only those values:
        parameters = {
            "info": "info",
            "aclass": "currency"
        }

        # Asset is not required
        if len(assets) != 0:
            parameters["asset"] = assets

        return self.public("Assets", parameters)

    def asset_pairs(self, info="info", pairs=""):
        """
            {  
                "error":[  
            
                ],
                "result":{  
                    "XXRPXXBT":{  
                        "pair_decimals":8,
                        "lot":"unit",
                        "margin_call":80,
                        "fees_maker":[  
                            [  
                                0,
                                0.16
                            ],
                            ...
                        ],
                        "altname":"XRPXBT",
                        "quote":"XXBT",
                        "fees":[  
                            [  
                                0,
                                0.26
                            ],
                            ...
                        ],
                        "aclass_quote":"currency",
                        "margin_stop":40,
                        "base":"XXRP",
                        "lot_multiplier":1,
                        "fee_volume_currency":"ZUSD",
                        "aclass_base":"currency",
                        "leverage_sell":[  
            
                        ],
                        "leverage_buy":[  
            
                        ],
                        "lot_decimals":8
                    },
                    ...
                }
            }

        """
        if info not in ["info", "leverage", "fees", "margin"]:
            raise ValueError("Value % is not a valid info string.".format(info))

        parameters = {
            "info": info,
        }

        # Pair is not required and should be omnited if empty
        if len(pairs) != 0:
            parameters["pair"] = pairs

        return self.public("AssetPairs", parameters)

    def ticker(self, pairs):
        """
        {  
            "error":[  
        
            ],
            "result":{  
                "XZECZEUR":{  
                    "t":[  
                        789,
                        1563
                    ],
                    "h":[  
                        "93.88889",
                        "93.88889"
                    ],
                    "l":[  
                        "83.30000",
                        "82.90067"
                    ],
                    "a":[  
                        "91.13167",
                        "1",
                        "1.000"
                    ],
                    "b":[  
                        "91.13166",
                        "1",
                        "1.000"
                    ],
                    "v":[  
                        "1409.83478992",
                        "3185.73131989"
                    ],
                    "p":[  
                        "90.08671",
                        "87.74001"
                    ],
                    "c":[  
                        "91.13068",
                        "3.23282073"
                    ],
                    "o":"85.87561"
                }
            }
        }
        """
        parameters = {
            "pair": pairs
        }

        if len(pairs) == 0:
            raise ValueError("Ticker pairs parameter is required.")

        return self.public("Ticker", parameters)

    def ohlc(self, pairs, interval=1, since=0) -> dict:
        """
            {  
                "error":[  
            
                ],
                "result":{  
                    "last":1494422340,
                    "XZECZEUR":[  
                        [  
                            1494379260,
                            "86.93479",
                            "86.93479",
                            "86.93479",
                            "86.93479",
                            "0.00000",
                            "0.00000000",
                            0
                        ],
                        ...
                    ]
                }
            }
        """
        if interval not in [1, 5, 15, 30, 60, 240, 1440, 10080, 21600]:
            raise ValueError("Interval parameter value '%' is not valid.".format(interval))

        parameters = {
            "pair": pairs,
            "interval": interval
        }

        if since != 0:
            parameters["since"] = since

        return self.public("OHLC", parameters)

    def depth(self, pairs, count=0):
        """  
        {  
            "error":[  
        
            ],
            "result":{  
                "XZECZEUR":{  
                    "asks":[  
                        [  
                            "89.92088",
                            "34.910",
                            1494422730
                        ],
                        ...
                    ],
                    "bids":[  
                        [  
                            "88.42616",
                            "4.755",
                            1494422729
                        ],
                        ...
                    ]
                }
            }
        }
        """
        parameters = {
            "pair": pairs
        }

        if count != 0:
            parameters["count"] = count

        return self.public("Depth", parameters)

    def trades(self, pairs, since=0):
        """       
        {  
            "error":[  
        
            ],
            "result":{  
                "last":"1494423192560021193",
                "XZECZEUR":[  
                    [  
                        "86.20035",
                        "0.44929000",
                        1494369147.0533,
                        "b",
                        "l",
                        ""
                    ],
                    ...
                ]
            }
        }
        """
        parameters = {
            "pair": pairs
        }

        if since != 0:
            parameters["since"] = since

        return self.public("Trades", parameters)

    def spread(self, pairs, since=0):
        """
        {  
            "error":[  
        
            ],
            "result":{  
                "XZECZEUR":[  
                    [  
                        1494423011,
                        "88.42539",
                        "88.91550"
                    ],
                    ...
                ],
                "last":1494423011
            }
        }
        """
        parameters = {
            "pair": pairs
        }

        if since != 0:
            parameters["since"] = since

        return self.public("Spread", parameters)

    def private(self, request, parameters=None):
        """
        Perform a private API call. 
        :warning:           Calling this function requires public and private keys to be set in class constructor.
        :param request:     One of ``Balance``, ``TradeBalance``, ``OpenOrders``, ``ClosedOrders``, ``QueryOrders``, \
                            ``TradesHistory``, ``QueryTrades``, ``OpenPositions``, ``Ledgers``, ``QueryLedgers``, \
                            ``TradeVolume``, ``AddOrder``, ``CancelOrder``.
        :param parameters:  Additional parameters for each request. See Kraken documentation for more information.
        :returns:           A JSON object representing Kraken API response.
        :raises:            ValueError is request string is not supported. ConnectionError and ConnectionTimeout on \
                            connection problem.
		"""

        parameters = parameters if parameters else {}

        # Check if request string is supported by this version of API
        if request not in self.supported_requests["private"]:
            raise ValueError("Request string '%' is not supported by private API calls".format(request))

        path = '/' + self.version + '/private/' + request

        # Nonce parameter is required. Each call should contain nonce with greater value than the previous one.
        parameters["nonce"] = int(time.time() * 1000)

        # Parse parameters to URL query string
        post = urllib.parse.urlencode(parameters)

        # UTF-8 string have to be encoded first
        encoded = (str(parameters['nonce']) + post).encode()

        # Message consist of path and hash of POST parameters
        message = path.encode() + hashlib.sha256(encoded).digest()


        try:
            signature = hmac.new(base64.b64decode(self._api_key), message, hashlib.sha512)
        except binascii.Error:
            raise ValueError("Private key is not a valid base64 encoded string")

        sigdigest = base64.b64encode(signature.digest())

        # Requred headers
        headers = {
            'API-Key': self._api_secret,
            'API-Sign': sigdigest.decode()
        }
        headers.update(self.headers)

        # Connect to API server
        try:
            response = requests.post(self.__api_url + path, data=parameters, headers=headers, timeout=self.timeout[0],
                                     proxies=self.proxy)
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(e.response)
        except requests.exceptions.Timeout:
            raise ConnectionTimeout()
        except requests.exceptions.TooManyRedirects:
            raise ConnectionError()

        if response.status_code != 200:
            raise ConnectionError()
        else:
            err_len = response.json()["error"]
            if len(err_len) > 0:
                raise ValueError(f"kraken API error: {err_len}")
            else:
                return response.json()["result"]

    def balance(self):
        return self.private("Balance")

    def trade_balance(self, asset="ZUSD"):
        parameters = {
            "aclass": "currency",
            "asset": asset
        }

        return self.private("TradeBalance", parameters)

    def open_orders(self, trades=False, userref=""):
        """
        Gets User opened orders. See `Kraken documentation <https://www.kraken.com/help/api#get-open-orders>`__.
        :param trades: Include trades in output? True/False.
        :param userref: Restrict results to given user reference ID.
        :return: Response as JSON object.
        :raises: Any of private method exceptions.
        """

        parameters = {
            "trades": "true" if trades else "false",
        }

        if len(userref) != 0:
            parameters["userref"] = userref

        return self.private("OpenOrders", parameters)

    def closed_orders(self, trades=False, userref="", start="", end="", offset="", closetime="both"):
        """
        Returns closed orders according to parameters. See `Kraken documentation <https://www.kraken.com/help/api#get-closed-orders>`__.
        :param trades: Include trades in response?
        :param userref: Restrict response to given user reference ID.
        :param start: Starting timestamp or order ID.
        :param end: End timestamp or order ID.
        :param offset: Result offset.
        :param closetime: Which time to use. One of ``open``, ``close``, ``both``.
        :return: Response as JSON object.
        :raises: Any of private method exceptions.
        """

        parameters = {
            "trades": "true" if trades else "false"
        }

        if len(userref) != 0:
            parameters["userref"] = userref

        if len(start) != 0:
            parameters["start"] = start

        if len(end) != 0:
            parameters["end"] = end

        if len(offset) != 0:
            parameters["offset"] = offset

        if closetime not in ["open", "close", "both"]:
            raise ValueError("Parameter closetime is not valid.")

        parameters["closetime"] = closetime

        return self.private("CloseOrders", parameters)

    def query_orders(self, trades=False, userref="", txid=""):
        """
        Returns orders info. See `Kraken documentation <https://www.kraken.com/help/api#query-orders-info>`__.
        :param trades: Include trades in output?
        :param userref: User reference ID.
        :param txid: Comma separated list of transaction IDs. Max 2O.
        :return: Response as JSON object.
        :raises: Any of private method exceptions.
        """

        parameters = {
            "trades": "true" if trades else "false"
        }

        if len(userref) != 0:
            parameters["userref"] = userref

        if len(txid) != 0:
            if len(txid.split(",")) > 20:
                raise ValueError("Parameter txid can not contain more than 20 comma separated values.")
            parameters["txid"] = txid

        return self.private("QueryOrders", parameters)

    def trades_history(self, ttype="all", trades=False, start="", end="", offset=""):
        """
        Gets trades history. See `Kraken documentation <https://www.kraken.com/help/api#get-trades-history>`__.
        :param ttype: Trade type. Method checks right input - it can be one of ``all``, ``any``, ``closed``, ``no``.
        :param trades: Include trades related to position in result?
        :param start: Unix timestamp or trade ID.
        :param end: Unix timestamp of trade ID.
        :param offset: History offset.
        :return: Response as JSON object.
        :raises: Any of private method exceptions.
        """

        if type not in ["all", "any", "closed", "closing", "no"]:
            raise ValueError("Type parameter is not valid.")

        parameters = {
            "type": ttype,
            "trades": "true" if trades else "false"
        }

        if len(start) != 0:
            parameters["start"] = start

        if len(end) != 0:
            parameters["end"] = end

        if len(offset) != 0:
            parameters["ofs"] = offset

        return self.private("TradesHistory", parameters)

    def query_trades(self, trades=False, txid=""):
        """
        Returns trade info. See `Kraken documentation <https://www.kraken.com/help/api#query-trades-info>`__.
        :param trades: Include trades related to position in response.
        :param txid: Comma separated list of transaction IDs. Max 2O.
        :return: Response as JSON object.
        :raises: Any of private method exceptions.
        """

        parameters = {
            "trades": "true" if trades else "false"
        }

        if len(txid) != 0:
            if len(txid.split(",")) > 20:
                raise ValueError("Parameter txid can not contain more than 20 comma separated values.")
            parameters["txid"] = txid

        return self.private("QueryTrades", parameters)

    def open_positions(self, docalcs=False, txid=""):
        """
        Returns open positions list. See `Kraken documentation <https://www.kraken.com/help/api#get-open-positions>`__.
        :param txid: Comma delimited list of transaction IDs to restrict output to
        :param docalcs: Include profit/loss calculations.
        :return: Response as JSON object.
        :raises: Any of private method exceptions.
        """

        parameters = {
            "docals": "true" if docalcs else "false"
        }

        if len(txid) != 0:
            if len(txid.split(",")) > 20:
                raise ValueError("Parameter txid can not contain more than 20 comma separated values.")
            parameters["txid"] = txid

        return self.private("OpenPositions", parameters)

    def ledgers(self, asset="", ltype="all", start=0, end=0, offset=0):
        """
        Returns ledgers list. See `Kraken documentation <https://www.kraken.com/help/api#get-ledgers-info>`__.
        :param str  asset:  Comma delimited list of assets to restrict output to.
        :param str  ltype:          Type of ledger to retrieve. One of ``all``, ``deposit``, ``withdrawal`` , \
                                    ``trade`` and ``margin``.
        :param int or str   start:  Starting unix timestamp or ledger ID of results.
        :param int or str   end:    Ending unix timestamp or ledger ID of results.
        :param int          offset: Result offset.
        :return:                    Response as JSON object.
        :raises:                    Any of private method exceptions.
        """
        if ltype not in ["all", "deposit", "withdrawal", "trade", "margin"]:
            raise ValueError("Parameter type is not valid")

        parameters = {
            "type": ltype,
            "aclass": "currency"
        }

        if len(asset) != 0:
            parameters["asset"] = asset

        if start != 0:
            parameters["start"] = start

        if end != 0:
            parameters["end"] = end

        if offset != 0:
            parameters["offset"] = offset

        return self.private("Ledgers", parameters)

    def query_ledgers(self, lid):
        """
        Returns ledger info. See `Kraken documentation <https://www.kraken.com/help/api#query-ledgers>`__.
        :param lid: Comma delimited list of ledger ids to query info about. Max 2O.
        :return: Response as JSON object.
        :raises: Any of private method exceptions.
        """

        parameters = {}

        if len(lid) != 0:
            if len(lid.split(",")) > 20:
                raise ValueError("Parameter id can not contain more than 20 comma separated values.")
            parameters["id"] = lid

        return self.private("QueryLedgers", parameters)

    def trade_volume(self, pair="", fee_info=False):
        """
        Gets trade volume. See `Kraken documentation <https://www.kraken.com/help/api#get-trade-volume>`__.
        :param pair: Comma delimited list of asset pairs to get fee info on.
        :param fee_info: Include fee info in results?
        :return: Response as JSON object.
        :raises: Any of private method exceptions.
        """
        parameters = {}

        if len(pair) != 0:
            if len(pair.split(",")) > 20:
                raise ValueError("Parameter pair can not contain more than 20 comma separated values.")
            parameters["pair"] = pair

        if fee_info:
            parameters["fee-info"] = "true"

        self.private("TradeVoluem", parameters)

    def add_order(self, pair, otype, ordertype, price, volume, price2=-1, leverage="none",
                  oflags="", starttm=0, expiretm=0, userref="", validate=False):
        """
        Adds exchange order to your account. See `Kraken documentation <https://www.kraken.com/help/api#add-standard-order>`__.
        :param pair: Asset pair.
        :param otype: Type of order (buy/sell).
        :param ordertype: Order type. Method tests right input to this parameter and thus may raise ``ValueError``.
		Only following values are allowed - ``market``, ``stop-loss``, ``take-profit``, ``stop-loss-profit``,
		``stop-loss-profit-limit``, ``stop-loss-limit``, ``take-profit-limit``, ``trailing-stop``, ``trailing-stop-limit``
		``stop-loss-and-limit`` and ``settle-position``.
		:param price: Price, meaning depends on order type.
		:param volume: Order volume in lots.
        :param price2: Price, meaning depends on order type.
        :param leverage: Amount of desired leverage.
        :param oflags: Comma separated flags: "viqc", "fcib", "fciq", "nompp".
        :param starttm: Scheduled start time. Zero (now) or unix timestamp.
        :param expiretm: Expiration time. Zero (never) or unix timestamp.
        :param userref: User reference id.  32-bit signed number.
        :param validate: Calidate inputs only. Do not submit order.
        :return: Response as JSON object.
        :raises: Any of private method exceptions.
        """
        if type not in ["buy", "sell"]:
            raise ValueError("Parameter type is not valid")

        if ordertype not in [
            "market" "stop-loss", "take-profit", "stop-loss-profit", "stop-loss-profit-limit",
            "stop-loss-limit", "take-profit-limit", "trailing-stop", "trailing-stop-limit",
            "stop-loss-and-limit", "settle-position"
        ]:

            raise ValueError("Parameter ordertype is not valid")

        parameters = {
            "pair": pair,
            "type": otype,
            "ordertype": ordertype,
            "price": price,
            "volume": volume,
            "leverage": leverage,
            "starttm": starttm,
            "expiretm": expiretm,
        }

        if price2 != -1:
            parameters["price2"] = price2

        if len(oflags) != 0:
            parameters["oflags"] = oflags

        if len(userref) != 0:
            parameters["userref"] = userref

        if validate:
            parameters["validate"] = "true"

        return self.private("AddOrder", parameters)

    def cancel_order(self, txid):
        """
        Cancels order. See `Kraken documentation <https://www.kraken.com/help/api#cancel-open-order>`__.
        :param txid: Transaction id.
        :return: Response as JSON object.
        :raises: Any of private method exceptions.
        """
        parameters = {
            "txid": txid
        }

        return self.private("CancelOrder", parameters)

class ConnectionTimeout(Exception):

    pass
        