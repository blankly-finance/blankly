"""
    Script for managing the variety of tickers on different exchanges.
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


from Blankly.exchanges.Coinbase_Pro.Coinbase_Pro_Tickers import Tickers as Coinbase_Pro_Ticker


class TickerManager:
    def __init__(self, default_exchange, default_currency):
        """
        Create a new manager.
        Args:
            default_exchange: Add an exchange name for the manager to favor
            default_currency: Add a default currency for the manager to favor
        """
        self.__default_exchange = default_exchange
        self.__default_currency = default_currency
        self.__tickers = {}
        self.__tickers[default_exchange] = {}

    """ 
    Manager Functions 
    """
    def create_ticker(self, callback, log=None, currency_id=None, override_exchange=None):
        """
        Create a ticker on a given exchange.
        Args:
            callback: Callback object for the function. Should be something like self.price_event
            log: Fill this with a path to log the price updates.
            currency_id: The currency to create a ticker for.
            override_exchange: Override the default exchange.
        Returns:
            Direct ticker object
        """
        exchange_name = self.__default_exchange
        # Ensure the ticker dict has this overridden exchange
        if override_exchange is not None:
            if override_exchange not in self.__tickers.keys():
                self.__tickers[override_exchange] = {}
            # Write this value so it can be used later
            exchange_name = override_exchange

        if exchange_name == "coinbase_pro":
            if currency_id is None:
                currency_id = self.__default_currency

            ticker = Coinbase_Pro_Ticker(currency_id, log=log)
            ticker.append_callback(callback)
            # Store this object
            self.__tickers['coinbase_pro'][currency_id] = ticker
            return ticker
        else:
            print(exchange_name + " ticker not supported, skipping creation")

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
        return currency_id, exchange

    def get_default_exchange_name(self):
        return self.__default_exchange

    def get_ticker(self, currency_id, override_default_exchange_name=None):
        """
        Retrieve the ticker attached to a currency
        Args:
            currency_id: The currency ID of ticker (required) such as "BTC-USD"
            override_default_exchange_name: Override the default to get tickers for different exchanges
        """
        if override_default_exchange_name is None:
            return self.__tickers[self.__default_exchange][currency_id]
        else:
            return self.__tickers[override_default_exchange_name][currency_id]

    def get_all_tickers(self):
        """
        Get the tickers object dictionary
        Returns:
            Dictionary with tickers referenced for each currency
        """
        return self.__tickers

    def delete_ticker(self, exchange, currency):
        """
        Deletes the ticker on the specified exchange currency
        Args:
            exchange: Exchange name such as "coinbase_pro"
            currency: Currency to remove, such as "BTC-USd"
        """
        self.__tickers[exchange][currency].close_websocket()
        del self.__tickers[exchange][currency]

    """ 
    Ticker Functions 
    """
    def append_callback(self, callback_object, override_currency_id=None, override_exchange=None):
        """
        Add another object to have the price_event() function called.
        Generally the callback object should be "self" and the callback_name should only be filled if you want to
        override the default "price_event()" function call.
        This can be very useful in working with multiple tickers, but not necessary on a simple bot.

        Args:
            callback_object: Reference for the callback function. The price_event(self, tick)
                function would be passed in as just self.price_event  -- no parenthesis or arguments, just the object
            override_currency_id: Ticker id, such as "BTC-USD" or exchange equivalents.
            override_exchange: Forces the manager to use a different supported exchange.
        """
        if override_currency_id is None:
            override_currency_id = self.__default_currency

        if override_exchange is None:
            override_exchange = self.__default_exchange

        if override_exchange == "coinbase_pro":
            self.__tickers['coinbase_pro'][override_currency_id].append_callback(callback_object)

    def is_websocket_open(self, override_currency=None, override_exchange=None):
        """
        Check if the websocket attached to a currency is open
        """
        currency_id, exchange = self.__evaluate_overrides(override_currency, override_exchange)
        if self.__default_exchange == "coinbase_pro":
            return self.__tickers[exchange][currency_id].is_websocket_open()

    def get_most_recent_tick(self, override_currency=None, override_exchange=None):
        """
        Get the most recent tick received
        """
        currency_id, exchange = self.__evaluate_overrides(override_currency, override_exchange)
        if self.__default_exchange == "coinbase_pro":
            """
            Returns:
                {'type': 'ticker', 'sequence': 23300178473, 'product_id': 'BTC-USD', 'price': '58833.23', 
                'open_24h': '57734.69', 'volume_24h': '16926.11727388', 'low_24h': '57000', 'high_24h': '59397.48', 
                'volume_30d': '585271.95796211', 'best_bid': '58833.22', 'best_ask': '58833.23', 'side': 'buy', 
                'time': '2021-03-30T15:21:23.201930Z', 'trade_id': 151058458, 'last_size': '0.00121711'}
            """
            return self.__tickers[exchange][currency_id].get_most_recent_tick()

    def get_most_recent_time(self, override_currency=None, override_exchange=None):
        """
        Get the most recent time associated with the most recent tick
        """
        currency_id, exchange = self.__evaluate_overrides(override_currency, override_exchange)
        if self.__default_exchange == "coinbase_pro":
            return self.__tickers[exchange][currency_id].get_most_recent_time()

    def get_time_feed(self, override_currency=None, override_exchange=None):
        """
        Get a time array associated with the ticker feed.
        """
        currency_id, exchange = self.__evaluate_overrides(override_currency, override_exchange)
        if self.__default_exchange == "coinbase_pro":
            return self.__tickers[exchange][currency_id].get_time_feed()

    def get_ticker_feed(self, override_currency=None, override_exchange=None):
        """
        Get the full ticker array. This can be extremely large.
        """
        currency_id, exchange = self.__evaluate_overrides(override_currency, override_exchange)
        if self.__default_exchange == "coinbase_pro":
            return self.__tickers[exchange][currency_id].get_ticker_feed()

    def get_response(self, override_currency=None, override_exchange=None):
        """
        Get the exchange's response to the request to subscribe to a feed
        """
        currency_id, exchange = self.__evaluate_overrides(override_currency, override_exchange)
        if self.__default_exchange == "coinbase_pro":
            return self.__tickers[exchange][currency_id].get_response()

    def close_websocket(self, override_currency=None, override_exchange=None):
        """
        Close a websocket thread
        """
        currency_id, exchange = self.__evaluate_overrides(override_currency, override_exchange)
        if self.__default_exchange == "coinbase_pro":
            self.__tickers[exchange][currency_id].close_websocket()

    def restart_ticker(self, override_currency=None, override_exchange=None):
        """
        Restart a websocket feed after asking it to stop
        """
        currency_id, exchange = self.__evaluate_overrides(override_currency, override_exchange)
        if self.__default_exchange == "coinbase_pro":
            self.__tickers[exchange][currency_id].restart_ticker()
