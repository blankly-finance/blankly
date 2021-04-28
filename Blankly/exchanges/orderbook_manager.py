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
import Blankly.utils.utils

from Blankly.exchanges.Coinbase_Pro.orderbook_websocket import OrderBook as Coinbase_Pro_Orderbook
from Blankly.exchanges.Binance.Binance_Websocket import Tickers as Binance_Orderbook
from Blankly.exchanges.IExchange_Websocket import IExchangeWebsocket


class OrderbookManger(IExchangeWebsocket):
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

    def create_orderbook(self, callback, currency_id=None, override_exchange=None):
        """
        Create an orderbook for a given exchange
        Args:
            callback: Callback object for the function. Should be something like self.price_event
            currency_id: Override the default currency id
            override_exchange: Override the default exchange
        """
        exchange_name = self.__default_exchange
        # Ensure the ticker dict has this overridden exchange
        if override_exchange is not None:
            if override_exchange not in self.__websockets.keys():
                self.__websockets[override_exchange] = {}
                self.__websockets_callbacks[override_exchange] = {}
            # Write this value so it can be used later
            exchange_name = override_exchange

        if exchange_name == "coinbase_pro":
            if currency_id is None:
                currency_id = self.__default_currency
            websocket = Coinbase_Pro_Orderbook(currency_id)
            # This is where the sorting magic happens
            websocket.append_callback(self.coinbase_update)
            websocket.append_snapshot_callback(self.coinbase_snapshot_update)
            # Store this object
            self.__websockets['coinbase_pro'][currency_id] = websocket
            self.__websockets_callbacks['coinbase_pro'][currency_id] = callback
            self.__orderbooks['coinbase_pro'][currency_id] = {
                "buy": {},
                "sell": {}
            }
            return websocket
        elif exchange_name == "binance":
            if currency_id is None:
                currency_id = self.__default_currency

            specific_currency_id = Blankly.utils.to_exchange_coin_id(currency_id, "binance").lower()
            websocket = Binance_Orderbook(specific_currency_id, "depth")
            websocket.append_callback(self.binance_update)

            # Binance returns the keys in all UPPER so the books should be created based on response
            specific_currency_id = specific_currency_id.upper()
            self.__websockets['binance'][specific_currency_id] = websocket
            self.__websockets_callbacks['binance'][specific_currency_id] = callback
            # TODO need an API object to get the depth snapshot
            self.__orderbooks['binance'][specific_currency_id] = {
                "buy": {},
                "sell": {}
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
        self.__websockets_callbacks['coinbase_pro'][update['product_id']](book)

    def binance_update(self, update):
        # TODO this needs a snapshot to work correctly
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
        self.__websockets_callbacks['binance'][symbol](self.__orderbooks['binance'][symbol])

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

        # if override_exchange == "coinbase_pro":
        self.__websockets_callbacks[override_exchange][override_currency_id] = callback_object

    def __evaluate_overrides(self, override_currency, override_exchange):
        """
        Switches to inputted exchanges, used in the public methods
        """
        # Issues could arise if the user specifies a different exchange but not a different currency. It would run
        # that default on the new exchange. Not great behavior unless they're clever
        if override_currency is not None:
            currency_id = override_currency
        else:
            currency_id = self.__default_currency
        if override_exchange is not None:
            exchange = override_exchange
        else:
            exchange = self.__default_exchange

        if exchange == "binance":
            currency_id = Blankly.utils.to_exchange_coin_id(currency_id, "binance")
        return currency_id, exchange

    """
    Websocket functions
    """
    def append_callback(self, callback_object, override_currency_id=None, override_exchange=None):
        """
        This is a bit different than above. This will give the direct feed of the websocket instead of a sorted book.
        Generally the callback object should be "self" and the callback_name should only be filled if you want to
        override the default "price_event()" function call.
        This can be very useful in working with multiple tickers, but not necessary on a simple bot.

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

        # if override_exchange == "coinbase_pro":
        self.__websockets[override_exchange][override_currency_id].append_callback(callback_object)

    def is_websocket_open(self, override_currency=None, override_exchange=None):
        """
        Check if the websocket attached to a currency is open
        """
        currency_id, exchange = self.__evaluate_overrides(override_currency, override_exchange)
        # if self.__default_exchange == "coinbase_pro":
        return self.__websockets[exchange][currency_id].is_websocket_open()

    def get_most_recent_tick(self, override_currency=None, override_exchange=None):
        """
        Get the most recent tick received
        """
        currency_id, exchange = self.__evaluate_overrides(override_currency, override_exchange)
        # if self.__default_exchange == "coinbase_pro":
        # TODO fix the returned value below
        """
        Returns:
            {'type': 'ticker', 'sequence': 23300178473, 'product_id': 'BTC-USD', 'price': '58833.23', 
            'open_24h': '57734.69', 'volume_24h': '16926.11727388', 'low_24h': '57000', 'high_24h': '59397.48', 
            'volume_30d': '585271.95796211', 'best_bid': '58833.22', 'best_ask': '58833.23', 'side': 'buy', 
            'time': '2021-03-30T15:21:23.201930Z', 'trade_id': 151058458, 'last_size': '0.00121711'}
        """
        return self.__websockets[exchange][currency_id].get_most_recent_tick()

    def get_most_recent_time(self, override_currency=None, override_exchange=None):
        """
        Get the most recent time associated with the most recent tick
        """
        currency_id, exchange = self.__evaluate_overrides(override_currency, override_exchange)
        # if self.__default_exchange == "coinbase_pro":
        return self.__websockets[exchange][currency_id].get_most_recent_time()

    def get_time_feed(self, override_currency=None, override_exchange=None):
        """
        Get a time array associated with the ticker feed.
        """
        currency_id, exchange = self.__evaluate_overrides(override_currency, override_exchange)
        # if self.__default_exchange == "coinbase_pro":
        return self.__websockets[exchange][currency_id].get_time_feed()

    def get_feed(self, override_currency=None, override_exchange=None):
        """
        Get the full ticker array. This can be extremely large.
        """
        currency_id, exchange = self.__evaluate_overrides(override_currency, override_exchange)
        # if self.__default_exchange == "coinbase_pro":
        return self.__websockets[exchange][currency_id].get_feed()

    def get_response(self, override_currency=None, override_exchange=None):
        """
        Get the exchange's response to the request to subscribe to a feed
        """
        currency_id, exchange = self.__evaluate_overrides(override_currency, override_exchange)
        # if self.__default_exchange == "coinbase_pro":
        return self.__websockets[exchange][currency_id].get_response()

    def close_websocket(self, override_currency=None, override_exchange=None):
        """
        Close a websocket thread
        """
        currency_id, exchange = self.__evaluate_overrides(override_currency, override_exchange)
        # if self.__default_exchange == "coinbase_pro":
        self.__websockets[exchange][currency_id].close_websocket()

    def restart_ticker(self, override_currency=None, override_exchange=None):
        """
        Restart a websocket feed after asking it to stop
        """
        currency_id, exchange = self.__evaluate_overrides(override_currency, override_exchange)
        # if self.__default_exchange == "coinbase_pro":
        self.__websockets[exchange][currency_id].restart_ticker()

    def close_all_websockets(self):
        """
        Iterate through orderbooks and make sure they're closed
        """
        self.__recursive_close(self.__websockets)

    def __recursive_close(self, d):
        for k, v in d.items():
            if isinstance(v, dict):
                self.__recursive_close(v)
            else:
                d[k].close_websocket()
