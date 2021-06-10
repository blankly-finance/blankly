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
import Blankly.utils.utils

from Blankly.exchanges.Coinbase_Pro.Coinbase_Pro_Websocket import Tickers as Coinbase_Pro_Ticker
from Blankly.exchanges.Binance.Binance_Websocket import Tickers as Binance_Ticker

from Blankly.exchanges.websocket_manager import WebsocketManager


class TickerManager(WebsocketManager):
    def __init__(self, default_exchange, default_currency):
        """
        Create a new manager.
        Args:
            default_exchange: Add an exchange name for the manager to favor
            default_currency: Add a default currency for the manager to favor
        """
        self.__default_exchange = default_exchange
        if default_exchange == "binance":
            default_currency = Blankly.utils.to_exchange_coin_id(default_currency, "binance").lower()
        self.__default_currency = default_currency

        self.__tickers = {}
        self.__tickers[default_exchange] = {}

        # Create abstraction for writing many different managers
        super().__init__(self.__tickers, default_currency, default_exchange)

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
        preferences = Blankly.utils.load_user_preferences()
        sandbox_mode = preferences['settings']['use_sandbox_websockets']

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

            if sandbox_mode:
                ticker = Coinbase_Pro_Ticker(currency_id, "ticker", log=log,
                                             WEBSOCKET_URL="wss://ws-feed-public.sandbox.pro.coinbase.com")
            else:
                ticker = Coinbase_Pro_Ticker(currency_id, "ticker", log=log)

            ticker.append_callback(callback)
            # Store this object
            self.__tickers['coinbase_pro'][currency_id] = ticker
            return ticker
        elif exchange_name == "binance":
            if currency_id is None:
                currency_id = self.__default_currency

            currency_id = Blankly.utils.to_exchange_coin_id(currency_id, "binance").lower()
            if sandbox_mode:
                ticker = Binance_Ticker(currency_id, "trade", log=log, WEBSOCKET_URL="wss://testnet.binance.vision/ws")
            else:
                ticker = Binance_Ticker(currency_id, "trade", log=log)
            ticker.append_callback(callback)
            self.__tickers['binance'][currency_id] = ticker
            return ticker
        else:
            print(exchange_name + " ticker not supported, skipping creation")
