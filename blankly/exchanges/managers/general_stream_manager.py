"""
    Class for creating general websocket streams
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
from blankly.exchanges.interfaces.alpaca.alpaca_websocket import Tickers as Alpaca_Websocket
from blankly.exchanges.interfaces.binance.binance_websocket import Tickers as Binance_Websocket
from blankly.exchanges.interfaces.coinbase_pro.coinbase_pro_websocket import Tickers as Coinbase_Pro_Websocket
from blankly.exchanges.managers.websocket_manager import WebsocketManager


class GeneralManager(WebsocketManager):
    def __init__(self, default_exchange, default_symbol):
        self.__default_exchange = default_exchange
        self.__default_currency = default_symbol

        self.__websockets = {}

        super().__init__(self.__websockets, default_symbol, default_exchange)

    def create_general_connection(self, callback, channel, log=None, override_symbol=None, override_exchange=None):
        """
        Create a channel on any given stream on any exchange. This is not stored in the manager object, only returned.
        """
        asset_id_cache = self.__default_currency
        exchange_cache = self.__default_exchange

        if override_symbol is not None:
            asset_id_cache = override_symbol

        if override_exchange is not None:
            exchange_cache = override_exchange

        if channel not in self.__websockets.keys():
            self.__websockets[channel] = {}

        if exchange_cache not in self.__websockets[channel].keys():
            self.__websockets[channel][exchange_cache] = {}

        if asset_id_cache not in self.__websockets[channel][exchange_cache].keys():
            self.__websockets[channel][exchange_cache][asset_id_cache] = {}

        use_sandbox = self.preferences['settings']['use_sandbox_websockets']

        if exchange_cache == "coinbase_pro":
            if use_sandbox:
                websocket = Coinbase_Pro_Websocket(asset_id_cache, channel, log,
                                                   WEBSOCKET_URL="wss://ws-feed-public.sandbox.pro.coinbase.com")
            else:
                websocket = Coinbase_Pro_Websocket(asset_id_cache, channel, log)
            websocket.append_callback(callback)

            self.__websockets[channel][exchange_cache][asset_id_cache] = websocket

            return websocket
        elif exchange_cache == "binance":
            # Lower this to subscribe
            asset_id_cache = blankly.utils.to_exchange_symbol(asset_id_cache, "binance").lower()
            if use_sandbox:
                websocket = Binance_Websocket(asset_id_cache, channel, log,
                                              WEBSOCKET_URL="wss://testnet.binance.vision/ws")
            else:
                websocket = Binance_Websocket(asset_id_cache, channel, log)
            websocket.append_callback(callback)

            # Upper this to cache
            asset_id_cache = asset_id_cache.upper()
            self.__websockets[channel][exchange_cache][asset_id_cache] = websocket

            return websocket

        elif exchange_cache == "alpaca":
            stream = self.preferences['settings']['alpaca']['websocket_stream']

            asset_id_cache = blankly.utils.to_exchange_symbol(asset_id_cache, "alpaca")
            if use_sandbox:
                websocket = Alpaca_Websocket(asset_id_cache, channel, log,
                                             WEBSOCKET_URL=
                                             "wss://paper-api.alpaca.markets/stream/v2/{}/".format(stream))
            else:
                websocket = Alpaca_Websocket(asset_id_cache, channel, log,
                                             WEBSOCKET_URL="wss://stream.data.alpaca.markets/v2/{}/".format(stream))
            websocket.append_callback(callback)

            self.__websockets[channel][exchange_cache][asset_id_cache] = websocket

            return websocket

    """
    Create overriden method signatures
    """

    def append_callback(self, callback_object, channel, override_symbol=None, override_exchange=None):
        self.websockets = self.__websockets[channel]
        super().append_callback(callback_object, override_symbol, override_exchange)

    def is_websocket_open(self, channel, override_symbol=None, override_exchange=None):
        self.websockets = self.__websockets[channel]
        return super().is_websocket_open(override_symbol, override_exchange)

    def get_most_recent_time(self, channel, override_symbol=None, override_exchange=None):
        self.websockets = self.__websockets[channel]
        return super().get_most_recent_time(override_symbol, override_exchange)

    def get_time_feed(self, channel, override_symbol=None, override_exchange=None):
        self.websockets = self.__websockets[channel]
        return super().get_time_feed(override_symbol, override_exchange)

    def get_feed(self, channel, override_symbol=None, override_exchange=None):
        self.websockets = self.__websockets[channel]
        return super().get_feed(override_symbol, override_exchange)

    def get_response(self, channel, override_symbol=None, override_exchange=None):
        self.websockets = self.__websockets[channel]
        return super().get_response(override_symbol, override_exchange)

    def close_websocket(self, channel, override_symbol=None, override_exchange=None):
        self.websockets = self.__websockets[channel]
        return super().close_websocket(override_symbol, override_exchange)

    def restart_ticker(self, channel, override_symbol=None, override_exchange=None):
        self.websockets = self.__websockets[channel]
        return super().restart_ticker(override_symbol, override_exchange)

    def get_most_recent_tick(self, channel, override_symbol=None, override_exchange=None):
        self.websockets = self.__websockets[channel]
        return super().get_most_recent_tick(override_symbol, override_exchange)
