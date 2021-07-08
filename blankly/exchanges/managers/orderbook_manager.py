"""
    Class to manage the orderbook, adding, removing and updating - as well as provide user interaction
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
import blankly.utils.utils
import blankly.exchanges.auth.auth_constructor
import requests

from blankly.exchanges.interfaces.coinbase_pro.coinbase_pro_websocket import Tickers as Coinbase_Pro_Orderbook
from blankly.exchanges.interfaces.binance.binance_websocket import Tickers as Binance_Orderbook

from blankly.exchanges.managers.websocket_manager import WebsocketManager


def binance_snapshot(symbol, limit):
    # TODO this should be using the REST set that Arun puts in
    params = {
        "symbol": symbol,
        "limit": limit
    }
    response = requests.get("https://api.binance.com/api/v3/depth", params=params).json()
    try:
        buys_response = response['bids']
    except KeyError:
        raise KeyError(response)
    sells_response = response['asks']
    buys = {}
    sells = {}
    for i in buys_response:
        buys[float(i[0])] = float(i[1])
    for i in sells_response:
        sells[float(i[0])] = float(i[1])

    return buys, sells


class OrderbookManager(WebsocketManager):
    def __init__(self, default_exchange, default_currency):
        """
        Create a new orderbook manager
        Args:
            default_exchange: Add an exchange name for the manager to favor
            default_currency: Add a default currency for the manager to favor
        """
        self.__default_exchange = default_exchange
        self.__default_currency = default_currency

        self.__orderbooks = {}
        self.__orderbooks[default_exchange] = {}

        self.__websockets = {}
        self.__websockets[default_exchange] = {}

        self.__websockets_callbacks = {}
        self.__websockets_callbacks[default_exchange] = {}

        self.__websockets_kwargs = {}
        self.__websockets_kwargs[default_exchange] = {}

        # Create the abstraction for adding many managers
        super().__init__(self.__websockets, default_currency, default_exchange)

    def create_orderbook(self, callback, currency_id=None, override_exchange=None, initially_stopped=False, **kwargs):
        """
        Create an orderbook for a given exchange
        Args:
            callback: Callback object for the function. Should be something like self.price_event
            currency_id: Override the default currency id
            override_exchange: Override the default exchange
            initially_stopped: Keep the websocket stopped when created
            kwargs: Add any other parameters that should be passed into a callback function to identify
                it or modify behavior
        """
        exchange_name = self.__default_exchange
        # Ensure the ticker dict has this overridden exchange
        if override_exchange is not None:
            if override_exchange not in self.__websockets.keys():
                self.__websockets[override_exchange] = {}
                self.__websockets_callbacks[override_exchange] = {}
                self.__websockets_kwargs[override_exchange] = {}
            # Write this value so it can be used later
            exchange_name = override_exchange

        if exchange_name == "coinbase_pro":
            if currency_id is None:
                currency_id = self.__default_currency
            websocket = Coinbase_Pro_Orderbook(currency_id, "level2",
                                               pre_event_callback=self.coinbase_snapshot_update,
                                               initially_stopped=initially_stopped
                                               )
            # This is where the sorting magic happens
            websocket.append_callback(self.coinbase_update)

            # Store this object
            self.__websockets['coinbase_pro'][currency_id] = websocket
            self.__websockets_callbacks['coinbase_pro'][currency_id] = callback
            self.__websockets_kwargs['coinbase_pro'][currency_id] = kwargs
            self.__orderbooks['coinbase_pro'][currency_id] = {
                "buy": {},
                "sell": {}
            }
            return websocket
        elif exchange_name == "binance":
            if currency_id is None:
                currency_id = self.__default_currency

            # Lower the keys to subscribe
            specific_currency_id = blankly.utils.to_exchange_coin_id(currency_id, "binance").lower()
            websocket = Binance_Orderbook(specific_currency_id, "depth", initially_stopped=initially_stopped)
            websocket.append_callback(self.binance_update)

            # binance returns the keys in all UPPER so the books should be created based on response
            specific_currency_id = specific_currency_id.upper()
            self.__websockets['binance'][specific_currency_id] = websocket
            self.__websockets_callbacks['binance'][specific_currency_id] = callback
            self.__websockets_kwargs['binance'][specific_currency_id] = kwargs

            buys, sells = binance_snapshot(specific_currency_id, 1000)
            self.__orderbooks['binance'][specific_currency_id] = {
                "buy": buys,
                "sell": sells
            }

        else:
            print(exchange_name + " ticker not supported, skipping creation")

    def coinbase_snapshot_update(self, update):
        print("Orderbook snapshot acquired for: " + update['product_id'])
        # Clear whatever book we had
        book = {
            "buy": {},
            "sell": {}
        }
        # Get all bids
        buys = update['bids']
        # Convert these to float and write to our order dictionaries
        for i in range(len(buys)):
            buy = buys[i]
            book['buy'][float(buy[0])] = float(buy[1])

        sells = update['asks']
        for i in range(len(sells)):
            sell = sells[i]
            book['sell'][float(sell[0])] = float(sell[1])

        self.__orderbooks['coinbase_pro'][update['product_id']] = book

    def coinbase_update(self, update):
        # Side is first in tuple
        side = update['changes'][0][0]
        # Price is second
        price = float(update['changes'][0][1])
        book = self.__orderbooks['coinbase_pro'][update['product_id']][side]

        # Quantity at that point is third
        qty = float(update['changes'][0][2])
        if qty == 0:
            try:
                book.pop(price)
            except KeyError:
                pass
        else:
            book[price] = float(update['changes'][0][2])
        self.__orderbooks['coinbase_pro'][update['product_id']][side] = book
        self.__websockets_callbacks['coinbase_pro'][update['product_id']](book,
                                                                          **self.__websockets_kwargs['coinbase_pro']
                                                                          [update['product_id']])

    def binance_update(self, update):
        # TODO this needs a snapshot to work correctly, which needs arun's rest code
        # Get symbol first
        symbol = update['s']

        # Get symbol for orderbook
        book_buys = self.__orderbooks['binance'][symbol]['buy']
        book_sells = self.__orderbooks['binance'][symbol]['sell']
        # Buys are b
        new_buys = update['b']
        for i in new_buys:
            # Price is i[0], quantity is i[1]
            if float(i[1]) == 0:
                try:
                    book_buys.pop(float(i[0]))
                except KeyError:
                    pass
            else:
                book_buys[float(i[0])] = float(i[1])
        # Asks are sells
        new_sells = update['a']
        for i in new_sells:
            # Price is i[0], quantity is i[1]
            if float(i[1]) == 0:
                try:
                    book_sells.pop(float(i[0]))
                except KeyError:
                    pass
            else:
                book_sells[float(i[0])] = float(i[1])
        self.__orderbooks['binance'][symbol]['buy'] = book_buys
        self.__orderbooks['binance'][symbol]['sell'] = book_sells
        # Pass in this new updated orderbook
        self.__websockets_callbacks['binance'][symbol](self.__orderbooks['binance'][symbol],
                                                       **self.__websockets_kwargs['binance'][symbol])

    def append_orderbook_callback(self, callback_object, override_currency_id=None, override_exchange=None):
        """
        These are appended calls to a sorted orderbook. Functions added to this will be fired every time the orderbook
        changes.
        Args:
            callback_object: Reference for the callback function. The price_event(self, tick)
                function would be passed in as just self.price_event -- no parenthesis or arguments, just the reference
            override_currency_id: Ticker id, such as "BTC-USD" or exchange equivalents.
            override_exchange: Forces the manager to use a different supported exchange.
        """
        if override_currency_id is None:
            override_currency_id = self.__default_currency

        if override_exchange is None:
            override_exchange = self.__default_exchange

        self.__websockets_callbacks[override_exchange][override_currency_id] = callback_object

    def get_most_recent_orderbook(self, override_currency_id=None, override_exchange=None):
        """
        Get the most recent orderbook under a currency and exchange.

        Args:
            override_currency_id: Ticker id, such as "BTC-USD" or exchange equivalents.
            override_exchange: Forces the manager to use a different supported exchange.
        """
        if override_currency_id is None:
            override_currency_id = self.__default_currency

        if override_exchange is None:
            override_exchange = self.__default_exchange

        return self.__orderbooks[override_exchange][override_currency_id]
