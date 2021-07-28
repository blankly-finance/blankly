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
import traceback
import warnings
from typing import List

import requests

import blankly.exchanges.auth.auth_constructor
import blankly.utils.utils
from blankly.exchanges.interfaces.alpaca.alpaca_websocket import Tickers as Alpaca_Websocket
from blankly.exchanges.interfaces.binance.binance_websocket import Tickers as Binance_Orderbook
from blankly.exchanges.interfaces.coinbase_pro.coinbase_pro_websocket import Tickers as Coinbase_Pro_Orderbook
from blankly.exchanges.managers.websocket_manager import WebsocketManager


def sort_list_tuples(list_with_tuples: list) -> List[tuple]:
    return sorted(list_with_tuples, key=lambda x: x[0])


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
    buys = []
    sells = []
    for i in buys_response:
        buys.append((float(i[0]), float(i[1])))
    for i in sells_response:
        sells.append((float(i[0]), float(i[1])))

    buys = sort_list_tuples(buys)
    sells = sort_list_tuples(sells)
    print("Orderbook snapshot acquired for: " + symbol.upper())
    return buys, sells


def remove_price(book: list, price: float) -> list:
    for j in range(len(book)):
        price_at_index = book[j][0]
        if price_at_index > price:
            break
        if price_at_index == price:
            book.pop(j)
            break

    return book


class OrderbookManager(WebsocketManager):
    def __init__(self, default_exchange, default_symbol):
        """
        Create a new orderbook manager
        Args:
            default_exchange: Add an exchange name for the manager to favor
            default_symbol: Add a default currency for the manager to favor
        """
        self.__default_exchange = default_exchange
        self.__default_currency = default_symbol

        self.__orderbooks = {}
        self.__orderbooks[default_exchange] = {}

        self.__websockets = {}
        self.__websockets[default_exchange] = {}

        self.__websockets_callbacks = {}
        self.__websockets_callbacks[default_exchange] = {}

        self.__websockets_kwargs = {}
        self.__websockets_kwargs[default_exchange] = {}

        # Create the abstraction for adding many managers
        super().__init__(self.__websockets, default_symbol, default_exchange)

    def create_orderbook(self, callback,
                         override_symbol=None,
                         override_exchange=None,
                         initially_stopped=False,
                         **kwargs):
        """
        Create an orderbook for a given exchange
        Args:
            callback: Callback object for the function. Should be something like self.price_event
            override_symbol: Override the default currency id
            override_exchange: Override the default exchange
            initially_stopped: Keep the websocket stopped when created
            kwargs: Add any other parameters that should be passed into a callback function to identify
                it or modify behavior
        """

        use_sandbox = self.preferences['settings']['use_sandbox_websockets']

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
            if override_symbol is None:
                override_symbol = self.__default_currency

            if use_sandbox:
                websocket = Coinbase_Pro_Orderbook(override_symbol, "level2",
                                                   pre_event_callback=self.coinbase_snapshot_update,
                                                   initially_stopped=initially_stopped,
                                                   WEBSOCKET_URL="wss://ws-feed-public.sandbox.pro.coinbase.com")
            else:
                websocket = Coinbase_Pro_Orderbook(override_symbol, "level2",
                                                   pre_event_callback=self.coinbase_snapshot_update,
                                                   initially_stopped=initially_stopped
                                                   )
            # This is where the sorting magic happens
            websocket.append_callback(self.coinbase_update)

            # Store this object
            self.__websockets['coinbase_pro'][override_symbol] = websocket
            self.__websockets_callbacks['coinbase_pro'][override_symbol] = [callback]
            self.__websockets_kwargs['coinbase_pro'][override_symbol] = kwargs
            self.__orderbooks['coinbase_pro'][override_symbol] = {
                "bids": [],
                "asks": []
            }
            return websocket
        elif exchange_name == "binance":
            if override_symbol is None:
                override_symbol = self.__default_currency

            # Lower the keys to subscribe
            specific_currency_id = blankly.utils.to_exchange_symbol(override_symbol, "binance").lower()

            if use_sandbox:
                websocket = Binance_Orderbook(specific_currency_id, "depth", initially_stopped=initially_stopped,
                                              WEBSOCKET_URL="wss://testnet.binance.vision/ws")
            else:
                websocket = Binance_Orderbook(specific_currency_id, "depth", initially_stopped=initially_stopped)

            websocket.append_callback(self.binance_update)

            # binance returns the keys in all UPPER so the books should be created based on response
            specific_currency_id = specific_currency_id.upper()
            self.__websockets['binance'][specific_currency_id] = websocket
            self.__websockets_callbacks['binance'][specific_currency_id] = [callback]
            self.__websockets_kwargs['binance'][specific_currency_id] = kwargs

            buys, sells = binance_snapshot(specific_currency_id, 1000)
            self.__orderbooks['binance'][specific_currency_id] = {
                "bids": buys,
                "asks": sells
            }

        elif exchange_name == "alpaca":
            warning_string = "Alpaca only allows the viewing of the bid/ask spread, not a total orderbook."
            warnings.warn(warning_string)
            if override_symbol is None:
                override_symbol = self.__default_currency

            stream = self.preferences['settings']['alpaca']['websocket_stream']
            override_symbol = blankly.utils.to_exchange_symbol(override_symbol, "alpaca")

            if use_sandbox:
                websocket = Alpaca_Websocket(override_symbol, 'quotes', initially_stopped=initially_stopped,
                                             WEBSOCKET_URL=
                                             "wss://paper-api.alpaca.markets/stream/v2/{}/".format(stream))
            else:
                websocket = Alpaca_Websocket(override_symbol, 'quotes', initially_stopped=initially_stopped,
                                             WEBSOCKET_URL="wss://stream.data.alpaca.markets/v2/{}/".format(stream))

            websocket.append_callback(self.alpaca_update)

            self.__websockets['alpaca'][override_symbol] = websocket
            self.__websockets_callbacks['alpaca'][override_symbol] = [callback]
            self.__websockets_kwargs['alpaca'][override_symbol] = kwargs

            self.__orderbooks['alpaca'][override_symbol] = {
                "bids": [],
                "asks": [],
            }

        else:
            print(exchange_name + " ticker not supported, skipping creation")

    def coinbase_snapshot_update(self, update):
        print("Orderbook snapshot acquired for: " + update['product_id'])
        # Clear whatever book we had
        book = {
            "bids": [],
            "asks": []
        }
        # Get all bids
        buys = update['bids']
        # Convert these to float and write to our order dictionaries
        for i in range(len(buys)):
            buy = buys[i]
            book['bids'].append((float(buy[0]), float(buy[1])))

        sells = update['asks']
        for i in range(len(sells)):
            sell = sells[i]
            book['asks'].append((float(sell[0]), float(sell[1])))

        book["bids"] = sort_list_tuples(book["bids"])
        book["asks"] = sort_list_tuples(book["asks"])

        self.__orderbooks['coinbase_pro'][update['product_id']] = book

    def coinbase_update(self, update):
        # Side is first in list
        side = update['changes'][0][0]

        # Have to convert coinbase to use this
        if side == 'buy':
            side = 'bids'
        elif side == 'sell':
            side = 'asks'

        # Price is second
        price = float(update['changes'][0][1])
        qty = float(update['changes'][0][2])
        book = self.__orderbooks['coinbase_pro'][update['product_id']][side]  # type: list

        # Quantity at that point is third
        if qty == 0:
            book = remove_price(book, price)
        else:
            book.append((price, qty))

        book = sort_list_tuples(book)
        self.__orderbooks['coinbase_pro'][update['product_id']][side] = book

        # Iterate through the callback list
        callbacks = self.__websockets_callbacks['coinbase_pro'][update['product_id']]
        for i in callbacks:
            i(self.__orderbooks['coinbase_pro'][update['product_id']],
              **self.__websockets_kwargs['coinbase_pro'][update['product_id']])

    def binance_update(self, update):
        try:
            # TODO this needs a snapshot to work correctly, which needs arun's rest code
            # Get symbol first
            symbol = update['s']

            # Get symbol for orderbook
            book_buys = self.__orderbooks['binance'][symbol]['bids']  # type: list
            book_sells = self.__orderbooks['binance'][symbol]['asks']  # type: list

            # Buys are b, count from low to high with reverse (which is the ::-1 thing)
            new_buys = update['b'][::-1]  # type: list
            for i in new_buys:
                i[0] = float(i[0])
                i[1] = float(i[1])
                if i[1] == 0:
                    book_buys = remove_price(book_buys, i[0])
                else:
                    book_buys.append((i[0], i[1]))

            # Asks are sells, these are also counted from low to high
            new_sells = update['a']  # type: list
            for i in new_sells:
                i[0] = float(i[0])
                i[1] = float(i[1])
                if i[1] == 0:
                    book_sells = remove_price(book_sells, i[0])
                else:
                    book_sells.append((i[0], i[1]))

            # Now sort them
            book_buys = sort_list_tuples(book_buys)
            book_sells = sort_list_tuples(book_sells)

            self.__orderbooks['binance'][symbol]['bids'] = book_buys
            self.__orderbooks['binance'][symbol]['asks'] = book_sells

            # Pass in this new updated orderbook
            callbacks = self.__websockets_callbacks['binance'][symbol]
            for i in callbacks:
                i(self.__orderbooks['binance'][symbol],
                  **self.__websockets_kwargs['binance'][symbol])
        except Exception:
            traceback.print_exc()

    def alpaca_update(self, update: dict):
        # Alpaca only gives the spread, no orderbook depth (alpaca is very bad)
        symbol = update['S']
        self.__orderbooks['alpaca'][symbol]['bids'] = [(update['bp'], update['bs'])]
        self.__orderbooks['alpaca'][symbol]['asks'] = [(update['ap'], update['as'])]

        callbacks = self.__websockets_callbacks['alpaca'][symbol]
        for i in callbacks:
            i(self.__orderbooks['alpaca'][symbol],
              **self.__websockets_kwargs['alpaca'][symbol])

    def append_orderbook_callback(self, callback_object, override_symbol=None, override_exchange=None):
        """
        These are appended calls to a sorted orderbook. Functions added to this will be fired every time the orderbook
        changes.
        Args:
            callback_object: Reference for the callback function. The price_event(self, tick)
                function would be passed in as just self.price_event -- no parenthesis or arguments, just the reference
            override_symbol: Ticker id, such as "BTC-USD" or exchange equivalents.
            override_exchange: Forces the manager to use a different supported exchange.
        """
        if override_symbol is None:
            override_symbol = self.__default_currency

        if override_exchange is None:
            override_exchange = self.__default_exchange

        self.__websockets_callbacks[override_exchange][override_symbol].append(callback_object)

    def get_most_recent_orderbook(self, override_symbol=None, override_exchange=None):
        """
        Get the most recent orderbook under a currency and exchange.

        Args:
            override_symbol: Ticker id, such as "BTC-USD" or exchange equivalents.
            override_exchange: Forces the manager to use a different supported exchange.
        """
        if override_symbol is None:
            override_symbol = self.__default_currency

        if override_exchange is None:
            override_exchange = self.__default_exchange

        return self.__orderbooks[override_exchange][override_symbol]
