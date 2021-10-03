"""
    This support calls to the Coinbase Pro API
    Copyright (c) 2017 Daniel Paquin, modified by Emerson Dove

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.
"""

import base64
import hashlib
import hmac
import json
import time

import requests
from requests.auth import AuthBase

# Create custom authentication for Exchange
from blankly.exchanges.auth.abc_auth import ABCAuth
from blankly.utils.utils import info_print


class CoinbaseExchangeAuth(AuthBase):
    # Provided by CBPro: https://docs.pro.coinbase.com/#signing-a-message
    def __init__(self, cb_auth: ABCAuth):
        self.api_key = cb_auth.keys['API_KEY']
        self.secret_key = cb_auth.keys['API_SECRET']
        self.passphrase = cb_auth.keys['API_PASS']

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
    def __init__(self, cb_auth: ABCAuth, API_URL='https://api.pro.coinbase.com/'):
        self.__auth = CoinbaseExchangeAuth(cb_auth)
        self.__api_url = API_URL
        self.session = requests.Session()

    """
    Public Client Calls
    """

    """ Full interface support """

    def get_products(self):
        """Get a list of available currency pairs for trading.

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
        return requests.get(self.__api_url + 'products', auth=self.__auth).json()

    def get_product_order_book(self, product_id, level=1):
        """Get a list of open orders for a product.

        The amount of detail shown can be customized with the `level`
        parameter:
        * 1: Only the best bid and ask
        * 2: Top 50 bids and asks (aggregated)
        * 3: Full order book (non aggregated)

        Level 1 and Level 2 are recommended for polling. For the most
        up-to-date data, consider using the websocket stream.

        **Caution**: Level 3 is only recommended for users wishing to
        maintain a full real-time order book using the websocket
        stream. Abuse of Level 3 via polling will cause your access to
        be limited or blocked.

        Args:
            product_id (str): Product
            level (Optional[int]): Order book level (1, 2, or 3).
                Default is 1.

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
            info_print("Abuse of polling at level 3 can result in a block. Consider using the websocket.")

        params = {'level': level}
        return requests.get(self.__api_url + "products/{}/book".format(product_id), params=params).json()

    """ PAGINATED """ """ Full interface support """

    def get_product_trades(self, product_id, before='', after='', limit=None, result=None):
        """List the latest trades for a product.

        This method returns a generator which may make multiple HTTP requests
        while iterating through it.

        Args:
             product_id (str): Product
             before (Optional[str]): start time in ISO 8601
             after (Optional[str]): end time in ISO 8601
             limit (Optional[int]): the desired number of trades (can be more than 100,
                          automatically paginated)
             result (Optional[list]): list of results that is used for the pagination
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
        return self._send_paginated_message('/products/{}/trades'
                                            .format(product_id))

    """ Full interface support """

    def get_product_historic_rates(self, product_id, start=None, end=None, granularity=None):
        """Historic rates for a product.

        Rates are returned in grouped buckets based on requested
        `granularity`. If start, end, and granularity aren't provided,
        the exchange will assume some (currently unknown) default values.

        Historical rate data may be incomplete. No data is published for
        intervals where there are no ticks.

        **Caution**: Historical rates should not be polled frequently.
        If you need real-time information, use the trade and book
        endpoints along with the websocket feed.

        The maximum number of data points for a single request is 200
        candles. If your selection of start/end time and granularity
        will result in more than 200 data points, your request will be
        rejected. If you wish to retrieve fine granularity data over a
        larger time range, you will need to make multiple requests with
        new start/end ranges.

        Args:
            product_id (str): Product
            start (Optional[str]): Start time in ISO 8601
            end (Optional[str]): End time in ISO 8601
            granularity (Optional[int]): Desired time slice in seconds

        Returns:
            list: Historic candle data. Example:
                [
                    [ time, low, high, open, close, volume ],
                    [ 1415398768, 0.32, 4.2, 0.35, 4.2, 12.3 ],
                    ...
                ]

        """
        params = {}
        if start is not None:
            params['start'] = start
        if end is not None:
            params['end'] = end

        params['granularity'] = granularity

        return requests.get(self.__api_url + 'products/{}/candles'.format(product_id), params=params).json()

    def get_product_24hr_stats(self, product_id):
        """Get 24 hr stats for the product.

        Args:
            product_id (str): Product

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
        return requests.get(self.__api_url + 'products/{}/stats'.format(product_id), auth=self.__auth).json()

    """ Full interface support """

    def get_currencies(self):
        """List known currencies.

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
        return requests.get(self.__api_url + 'currencies', auth=self.__auth).json()

    def get_time(self):
        """Get the API server time.

        Returns:
            dict: Server time in ISO and epoch format (decimal seconds
                since Unix epoch). Example::
                    {
                        "iso": "2015-01-07T23:47:25.201Z",
                        "epoch": 1420674445.201
                    }

        """
        return requests.get(self.__api_url + 'time', auth=self.__auth).json()

    """
    Private API Calls
    """

    def get_accounts(self):
        """ Get a list of trading all accounts.

        When you place an order, the funds for the order are placed on
        hold. They cannot be used for other orders or withdrawn. Funds
        will remain on hold until the order is filled or canceled. The
        funds on hold for each account will be specified.

        Returns:
            list: Info about all accounts. Example::
                [
                    {
                        "id": "71452118-efc7-4cc4-8780-a5e22d4baa53",
                        "currency": "BTC",
                        "balance": "0.0000000000000000",
                        "available": "0.0000000000000000",
                        "hold": "0.0000000000000000",
                        "profile_id": "75da88c5-05bf-4f54-bc85-5c775bd68254"
                    },
                    {
                        ...
                    }
                ]

        * Additional info included in response for margin accounts.
        """
        return requests.get(self.__api_url + 'accounts', auth=self.__auth).json()

    """ Full interface support """

    def get_account(self, account_id):
        """ Get information for a single account.

        Use this endpoint when you know the account_id.

        Args:
            account_id (str): Account id for account you want to get.

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
        return requests.get(self.__api_url + 'accounts/' + account_id, auth=self.__auth).json()

    """ PAGINATED """

    def get_account_history(self, account_id, **kwargs):
        """ List account activity. Account activity either increases or
        decreases your account balance.

        Entry type indicates the reason for the account change.
        * transfer:	Funds moved to/from Coinbase to cbpro
        * match:	Funds moved as a result of a trade
        * fee:	    Fee as a result of a trade
        * rebate:   Fee rebate as per our fee schedule

        If an entry is the result of a trade (match, fee), the details
        field will contain additional information about the trade.

        Args:
            account_id (str): Account id to get history of.
            kwargs (dict): Additional HTTP request parameters.

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
        """
        endpoint = '/accounts/{}/ledger'.format(account_id)
        return self._send_paginated_message(endpoint, params=kwargs)

    """ PAGINATED """

    def get_account_holds(self, account_id, **kwargs):
        """ Get holds on an account.

        This method returns a generator which may make multiple HTTP requests
        while iterating through it.

        Holds are placed on an account for active orders or
        pending withdraw requests.

        As an order is filled, the hold amount is updated. If an order
        is canceled, any remaining hold is removed. For a withdraw, once
        it is completed, the hold is removed.

        The `type` field will indicate why the hold exists. The hold
        type is 'order' for holds related to open orders and 'transfer'
        for holds related to a withdraw.

        The `ref` field contains the id of the order or transfer which
        created the hold.

        Args:
            account_id (str): Account id to get holds of.
            kwargs (dict): Additional HTTP request parameters.

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
        endpoint = '/accounts/{}/holds'.format(account_id)
        return self._send_paginated_message(endpoint, params=kwargs)

    """
    Buy & sell
    """

    def place_order(self, product_id, side, order_type, **kwargs):
        """ Place an order.

        The three order types (limit, market, and stop) can be placed using this
        method. Specific methods are provided for each order type, but if a
        more generic interface is desired this method is available.

        Args:
            product_id (str): Product to order (eg. 'BTC-USD')
            side (str): Order side ('buy' or 'sell)
            order_type (str): Order type ('limit', 'market', or 'stop')
            **client_oid (str): Order ID selected by you to identify your order.
                This should be a UUID, which will be broadcast in the public
                feed for `received` messages.
            **stp (str): Self-trade prevention flag. cbpro doesn't allow self-
                trading. This behavior can be modified with this flag.
                Options:
                'dc'	Decrease and Cancel (default)
                'co'	Cancel oldest
                'cn'	Cancel newest
                'cb'	Cancel both
            **overdraft_enabled (Optional[bool]): If true funding above and
                beyond the account balance will be provided by margin, as
                necessary.
            **funding_amount (Optional[Decimal]): Amount of margin funding to be
                provided for the order. Mutually exclusive with
                `overdraft_enabled`.
            **kwargs: Additional arguments can be specified for different order
                types. See the limit/market/stop order methods for details.

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
        # Margin parameter checks
        if kwargs.get('overdraft_enabled') is not None and \
                kwargs.get('funding_amount') is not None:
            raise ValueError('Margin funding must be specified through use of '
                             'overdraft or by setting a funding amount, but not'
                             ' both')

        # Limit order checks
        if order_type == 'limit':
            if kwargs.get('cancel_after') is not None and \
                    kwargs.get('time_in_force') != 'GTT':
                raise ValueError('May only specify a cancel period when time '
                                 'in_force is `GTT`')
            if kwargs.get('post_only') is not None and kwargs.get('time_in_force') in \
                    ['IOC', 'FOK']:
                raise ValueError('post_only is invalid when time in force is '
                                 '`IOC` or `FOK`')

        # Market and stop order checks
        if order_type == 'market' or order_type == 'stop':
            if not (kwargs.get('size') is None) ^ (kwargs.get('funds') is None):
                raise ValueError('Either `size` or `funds` must be specified '
                                 'for market/stop orders (but not both).')

        # Build params dict
        params = {'product_id': product_id,
                  'side': side,
                  'type': order_type}
        params.update(kwargs)
        return requests.post(self.__api_url + 'orders', data=json.dumps(params), auth=self.__auth).json()

    def place_limit_order(self, product_id, side, price, size,
                          client_oid=None,
                          stp=None,
                          time_in_force=None,
                          cancel_after=None,
                          post_only=None,
                          overdraft_enabled=None,
                          funding_amount=None):
        """Place a limit order.

        Args:
            product_id (str): Product to order (eg. 'BTC-USD')
            side (str): Order side ('buy' or 'sell)
            price (Decimal): Price per cryptocurrency
            size (Decimal): Amount of cryptocurrency to buy or sell
            client_oid (Optional[str]): User-specified Order ID
            stp (Optional[str]): Self-trade prevention flag. See `place_order`
                for details.
            time_in_force (Optional[str]): Time in force. Options:
                'GTC'   Good till canceled
                'GTT'   Good till time (set by `cancel_after`)
                'IOC'   Immediate or cancel
                'FOK'   Fill or kill
            cancel_after (Optional[str]): Cancel after this period for 'GTT'
                orders. Options are 'min', 'hour', or 'day'.
            post_only (Optional[bool]): Indicates that the order should only
                make liquidity. If any part of the order results in taking
                liquidity, the order will be rejected and no part of it will
                execute.
            overdraft_enabled (Optional[bool]): If true funding above and
                beyond the account balance will be provided by margin, as
                necessary.
            funding_amount (Optional[Decimal]): Amount of margin funding to be
                provided for the order. Mutually exclusive with
                `overdraft_enabled`.

        Returns:
            dict: Order details. See `place_order` for example.

        """
        params = {'product_id': product_id,
                  'side': side,
                  'order_type': 'limit',
                  'price': price,
                  'size': size,
                  'client_oid': client_oid,
                  'stp': stp,
                  'time_in_force': time_in_force,
                  'cancel_after': cancel_after,
                  'post_only': post_only,
                  'overdraft_enabled': overdraft_enabled,
                  'funding_amount': funding_amount}
        params = dict((k, v) for k, v in params.items() if v is not None)

        return self.place_order(**params)

    def place_market_order(self, product_id, side, size=None, funds=None,
                           client_oid=None,
                           stp=None,
                           overdraft_enabled=None,
                           funding_amount=None):
        """ Place market order.

        Args:
            product_id (str): Product to order (eg. 'BTC-USD')
            side (str): Order side ('buy' or 'sell)
            size (Optional[Decimal]): Desired amount in crypto. Specify this or
                `funds`.
            funds (Optional[Decimal]): Desired amount of quote currency to use.
                Specify this or `size`.
            client_oid (Optional[str]): User-specified Order ID
            stp (Optional[str]): Self-trade prevention flag. See `place_order`
                for details.
            overdraft_enabled (Optional[bool]): If true funding above and
                beyond the account balance will be provided by margin, as
                necessary.
            funding_amount (Optional[Decimal]): Amount of margin funding to be
                provided for the order. Mutually exclusive with
                `overdraft_enabled`.

        Returns:
            dict: Order details. See `place_order` for example.

        """
        params = {'product_id': product_id,
                  'side': side,
                  'order_type': 'market',
                  'size': size,
                  'funds': funds,
                  'client_oid': client_oid,
                  'stp': stp,
                  'overdraft_enabled': overdraft_enabled,
                  'funding_amount': funding_amount}
        params = dict((k, v) for k, v in params.items() if v is not None)
        return self.place_order(**params)

    def place_stop_order(self, product_id, side, price, size=None, funds=None,
                         client_oid=None,
                         stp=None,
                         overdraft_enabled=None,
                         funding_amount=None):
        """ Place stop order.

        Args:
            product_id (str): Product to order (eg. 'BTC-USD')
            side (str): Order side ('buy' or 'sell)
            price (Decimal): Desired price at which the stop order triggers.
            size (Optional[Decimal]): Desired amount in crypto. Specify this or
                `funds`.
            funds (Optional[Decimal]): Desired amount of quote currency to use.
                Specify this or `size`.
            client_oid (Optional[str]): User-specified Order ID
            stp (Optional[str]): Self-trade prevention flag. See `place_order`
                for details.
            overdraft_enabled (Optional[bool]): If true funding above and
                beyond the account balance will be provided by margin, as
                necessary.
            funding_amount (Optional[Decimal]): Amount of margin funding to be
                provided for the order. Mutually exclusive with
                `overdraft_enabled`.

        Returns:
            dict: Order details. See `place_order` for example.

        """
        params = {'product_id': product_id,
                  'side': side,
                  'price': price,
                  'order_type': 'stop',
                  'size': size,
                  'funds': funds,
                  'client_oid': client_oid,
                  'stp': stp,
                  'overdraft_enabled': overdraft_enabled,
                  'funding_amount': funding_amount}
        params = dict((k, v) for k, v in params.items() if v is not None)
        return self.place_order(**params)

    """ Full interface support """

    def cancel_order(self, order_id):
        """ Cancel a previously placed order.

        If the order had no matches during its lifetime its record may
        be purged. This means the order details will not be available
        with get_order(order_id). If the order could not be canceled
        (already filled or previously canceled, etc), then an error
        response will indicate the reason in the message field.

        **Caution**: The order id is the server-assigned order id and
        not the optional client_oid.

        Args:
            order_id (str): The order_id of the order you want to cancel

        Returns:
            list: Containing the order_id of cancelled order. Example::
                [ "c5ab5eae-76be-480e-8961-00792dc7e138" ]

        """
        return requests.delete(self.__api_url + 'orders/' + order_id, auth=self.__auth).json()

    """ PAGINATED """
    """ Full interface support (untested) """

    def get_orders(self, product_id=None, status=None, **kwargs):
        """ List your current open orders.

        This method returns a generator which may make multiple HTTP requests
        while iterating through it.

        Only open or un-settled orders are returned. As soon as an
        order is no longer open and settled, it will no longer appear
        in the default request.

        Orders which are no longer resting on the order book, will be
        marked with the 'done' status. There is a small window between
        an order being 'done' and 'settled'. An order is 'settled' when
        all of the fills have settled and the remaining holds (if any)
        have been removed.

        For high-volume trading it is strongly recommended that you
        maintain your own list of open orders and use one of the
        streaming market data feeds to keep it updated. You should poll
        the open orders endpoint once when you start trading to obtain
        the current state of any open orders.

        Args:
            product_id (Optional[str]): Only list orders for this
                product
            status (Optional[list/str]): Limit list of orders to
                this status or statuses. Passing 'all' returns orders
                of all statuses.
                ** Options: 'open', 'pending', 'active', 'done',
                    'settled'
                ** default: ['open', 'pending', 'active']

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
        params = kwargs
        if product_id is not None:
            params['product_id'] = product_id
        if status is not None:
            params['status'] = status
        return self._send_paginated_message('orders', params=params)

    """ Full interface support (untested) """

    def get_order(self, order_id):
        """ Get a single order by order id.

        If the order is canceled the response may have status code 404
        if the order had no matches.

        **Caution**: Open orders may change state between the request
        and the response depending on market conditions.

        Args:
            order_id (str): The order to get information of.

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
        return requests.get(self.__api_url + "orders/" + order_id, auth=self.__auth).json()

    """ PAGINATED """

    def get_fills(self, order_id=None, product_id=None, **kwargs):
        """ Get a list of recent fills.

        As of 8/23/18 - Requests without either order_id or product_id
        will be rejected

        This method returns a generator which may make multiple HTTP requests
        while iterating through it.

        Fees are recorded in two stages. Immediately after the matching
        engine completes a match, the fill is inserted into our
        datastore. Once the fill is recorded, a settlement process will
        settle the fill and credit both trading counterparties.

        The 'fee' field indicates the fees charged for this fill.

        The 'liquidity' field indicates if the fill was the result of a
        liquidity provider or liquidity taker. M indicates Maker and T
        indicates Taker.

        Args:
            product_id (str): Limit list to this product_id
            order_id (str): Limit list to this order_id
            kwargs (dict): Additional HTTP request parameters.

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
        if (product_id is None) and (order_id is None):
            raise ValueError('Either product_id or order_id must be specified.')

        params = {}
        if product_id:
            params['product_id'] = product_id
        if order_id:
            params['order_id'] = order_id
        params.update(kwargs)

        return self._send_paginated_message('/fills', params=params)

    """ Full interface support (tested) """

    def get_fees(self):
        """
            Returns:
            dict: Contains info about fees and volume. Example::
            {
                'maker_fee_rate': '0.0050',
                'taker_fee_rate': '0.0050',
                'usd_volume': '37.69'
            }
        """
        return requests.get(self.__api_url + "fees", auth=self.__auth).json()

    def _send_paginated_message(self, endpoint, params=None):
        """ Send API message that results in a paginated response.

        The paginated responses are abstracted away by making API requests on
        demand as the response is iterated over.

        Paginated API messages support 3 additional parameters: `before`,
        `after`, and `limit`. `before` and `after` are mutually exclusive. To
        use them, supply an index value for that endpoint (the field used for
        indexing varies by endpoint - get_fills() uses 'trade_id', for example).
            `before`: Only get data that occurs more recently than index
            `after`: Only get data that occurs further in the past than index
            `limit`: Set amount of data per HTTP response. Default (and
                maximum) of 100.

        Args:
            endpoint (str): Endpoint (to be added to base URL)
            params (Optional[dict]): HTTP request parameters

        Yields:
            dict: API response objects

        """
        if params is None:
            params = dict()
        while True:
            r = requests.get(self.__api_url + endpoint, params=params, auth=self.__auth, timeout=30)
            # r = self.session.get(url, params=params, auth=self.auth, timeout=30)
            results = r.json()
            for result in results:
                yield result
            # If there are no more pages, we're done. Otherwise update `after`
            # param to get next page.
            # If this request included `before` don't get any more pages - the
            # cbpro API doesn't support multiple pages in that case.
            if not r.headers.get('cb-after') or \
                    params.get('before') is not None:
                break
            else:
                params['after'] = r.headers['cb-after']

    """
    UNDOCUMENTED
    """

    def create_report(self, report_type, start_date, end_date, product_id=None,
                      account_id=None, report_format='pdf', email=None):
        """ Create report of historic information about your account.

        The report will be generated when resources are available. Report status
        can be queried via `get_report(report_id)`.

        Args:
            report_type (str): 'fills' or 'account'
            start_date (str): Starting date for the report in ISO 8601
            end_date (str): Ending date for the report in ISO 8601
            product_id (Optional[str]): ID of the product to generate a fills
                report for. Required if account_type is 'fills'
            account_id (Optional[str]): ID of the account to generate an account
                report for. Required if report_type is 'account'.
            report_format (Optional[str]): 'pdf' or 'csv'. Default is 'pdf'.
            email (Optional[str]): Email address to send the report to.

        Returns:
            dict: Report details. Example::
                {
                    "id": "0428b97b-bec1-429e-a94c-59232926778d",
                    "type": "fills",
                    "status": "pending",
                    "created_at": "2015-01-06T10:34:47.000Z",
                    "completed_at": undefined,
                    "expires_at": "2015-01-13T10:35:47.000Z",
                    "file_url": undefined,
                    "params": {
                        "start_date": "2014-11-01T00:00:00.000Z",
                        "end_date": "2014-11-30T23:59:59.000Z"
                    }
                }

        """
        params = {'type': report_type,
                  'start_date': start_date,
                  'end_date': end_date,
                  'format': report_format}
        if product_id is not None:
            params['product_id'] = product_id
        if account_id is not None:
            params['account_id'] = account_id
        if email is not None:
            params['email'] = email
        return requests.post(self.__api_url + "reports", data=json.dumps(params), auth=self.__auth).json()

    def get_report(self, report_id):
        """ Get report status.

        Use to query a specific report once it has been requested.

        Args:
            report_id (str): Report ID

        Returns:
            dict: Report details, including file url once it is created.

        """
        return requests.get(self.__api_url + "reports/" + report_id, auth=self.__auth).json()

    def get_trailing_volume(self):
        """  Get your 30-day trailing volume for all products.

        This is a cached value that's calculated every day at midnight UTC.

        Returns:
            list: 30-day trailing volumes. Example::
                [
                    {
                        "product_id": "BTC-USD",
                        "exchange_volume": "11800.00000000",
                        "volume": "100.00000000",
                        "recorded_at": "1973-11-29T00:05:01.123456Z"
                    },
                    {
                        ...
                    }
                ]

        """
        return requests.get(self.__api_url + "users/self/trailing-volume", auth=self.__auth).json()

    def get_coinbase_accounts(self):
        """ Get a list of your coinbase accounts.

        Returns:
            list: Coinbase account details.

        """
        return requests.get(self.__api_url + 'coinbase-accounts', auth=self.__auth).json()

    def get_product_ticker(self, product_id):
        """ Get recent market data for a product
        Use of this is discouraged, websocket feeds should be used instead for high speed polling.

        Returns:
            {
                "trade_id": 4729088,
                "price": "333.99",
                "size": "0.193",
                "bid": "333.98",
                "ask": "333.99",
                "volume": "5957.11914015",
                "time": "2015-11-14T20:46:03.511254Z"
            }
        """
        return requests.get(self.__api_url + 'products/' + product_id + '/ticker', auth=self.__auth).json()

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
#         self.__Utils = blankly.Utils.Utils()
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
