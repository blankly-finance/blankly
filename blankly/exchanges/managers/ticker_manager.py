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
import blankly.utils.utils
from blankly.exchanges.interfaces.alpaca.alpaca_websocket import Tickers as Alpaca_Ticker
from blankly.exchanges.interfaces.binance.binance_websocket import Tickers as Binance_Ticker
from blankly.exchanges.interfaces.coinbase_pro.coinbase_pro_websocket import Tickers as Coinbase_Pro_Ticker
from blankly.exchanges.managers.websocket_manager import WebsocketManager


class TickerManager(WebsocketManager):
    def __init__(self, default_exchange: str, default_symbol: str):
        """
        Create a new manager.
        Args:
            default_exchange: Add an exchange name for the manager to favor
            default_symbol: Add a default currency for the manager to favor
        """
        self.__default_exchange = default_exchange
        if default_exchange == "binance":
            default_symbol = blankly.utils.to_exchange_symbol(default_symbol, "binance").lower()
        elif default_exchange == "alpaca":
            default_symbol = blankly.utils.to_exchange_symbol(default_symbol, "alpaca")

        self.__default_symbol = default_symbol

        self.__tickers = {}
        self.__tickers[default_exchange] = {}

        # Create abstraction for writing many different managers
        super().__init__(self.__tickers, default_symbol, default_exchange)

    """ 
    Manager Functions 
    """

    def create_ticker(self, callback, log: str = None, override_symbol: str = None, override_exchange: str = None):
        """
        Create a ticker on a given exchange.
        Args:
            callback: Callback object for the function. Should be something like self.price_event
            log: Fill this with a path to log the price updates.
            override_symbol: The currency to create a ticker for.
            override_exchange: Override the default exchange.
        Returns:
            Direct ticker object
        """

        sandbox_mode = self.preferences['settings']['use_sandbox_websockets']

        exchange_name = self.__default_exchange
        # Ensure the ticker dict has this overridden exchange
        if override_exchange is not None:
            if override_exchange not in self.__tickers.keys():
                self.__tickers[override_exchange] = {}
            # Write this value so it can be used later
            exchange_name = override_exchange

        if exchange_name == "coinbase_pro":
            if override_symbol is None:
                override_symbol = self.__default_symbol

            if sandbox_mode:
                ticker = Coinbase_Pro_Ticker(override_symbol, "ticker", log=log,
                                             WEBSOCKET_URL="wss://ws-feed-public.sandbox.pro.coinbase.com")
            else:
                ticker = Coinbase_Pro_Ticker(override_symbol, "ticker", log=log)

            ticker.append_callback(callback)
            # Store this object
            self.__tickers['coinbase_pro'][override_symbol] = ticker
            return ticker
        elif exchange_name == "binance":
            if override_symbol is None:
                override_symbol = self.__default_symbol

            override_symbol = blankly.utils.to_exchange_symbol(override_symbol, "binance").lower()
            if sandbox_mode:
                ticker = Binance_Ticker(override_symbol,
                                        "trades",
                                        log=log,
                                        WEBSOCKET_URL="wss://testnet.binance.vision/ws")
            else:
                ticker = Binance_Ticker(override_symbol,
                                        "trades",
                                        log=log)
            ticker.append_callback(callback)
            self.__tickers['binance'][override_symbol] = ticker
            return ticker
        elif exchange_name == "alpaca":
            stream = self.preferences['settings']['alpaca']['websocket_stream']
            if override_symbol is None:
                override_symbol = self.__default_symbol

            override_symbol = blankly.utils.to_exchange_symbol(override_symbol, "alpaca")
            if sandbox_mode:
                ticker = Alpaca_Ticker(override_symbol,
                                       "trades",
                                       log=log,
                                       WEBSOCKET_URL="wss://paper-api.alpaca.markets/stream/v2/{}/".format(stream))
            else:
                ticker = Alpaca_Ticker(override_symbol,
                                       "trades",
                                       log=log,
                                       WEBSOCKET_URL="wss://stream.data.alpaca.markets/v2/{}/".format(stream))
            ticker.append_callback(callback)
            self.__tickers['alpaca'][override_symbol] = ticker
            return ticker

        else:
            print(exchange_name + " ticker not supported, skipping creation")
