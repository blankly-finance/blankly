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
import Blankly.utils.utils
from Blankly.exchanges.Coinbase_Pro.Coinbase_Pro_Websocket import Tickers as Coinbase_Pro_Websocket
from Blankly.exchanges.Binance.Binance_Websocket import Tickers as Binance_Websocket

from Blankly.exchanges.websocket_manager import WebsocketManager


class GeneralManager(WebsocketManager):
    def __init__(self, default_exchange, default_currency, default_channel):
        self.__default_exchange = default_exchange
        self.__default_currency = default_currency
        self.default_channel = default_channel

        self.__websockets = {}

        super().__init__(self.__websockets, default_currency, default_exchange)

    def create_general_connection(self, callback, channel, log=None, asset_id=None, override_exchange=None):
        """
        Create a channel on any given stream on any exchange. This is not stored in the manager object, only returned.
        """
        asset_id_cache = self.__default_currency
        exchange_cache = self.__default_exchange

        if asset_id is not None:
            asset_id_cache = asset_id

        if override_exchange is not None:
            exchange_cache = override_exchange

        preferences = Blankly.utils.load_user_preferences()

        if channel not in self.__websockets.keys():
            self.__websockets[channel] = {}

        if exchange_cache not in self.__websockets[channel].keys():
            self.__websockets[channel][exchange_cache] = {}

        if asset_id_cache not in self.__websockets[channel][exchange_cache].keys():
            self.__websockets[channel][exchange_cache][asset_id_cache] = {}

        use_sandbox = preferences['settings']['use_sandbox_websockets']

        if exchange_cache == "coinbase_pro":
            print(self.__websockets)
            if use_sandbox:
                websocket = Coinbase_Pro_Websocket(asset_id_cache, channel, log,
                                                   WEBSOCKET_URL="wss://ws-feed-public.sandbox.pro.coinbase.com")
            else:
                websocket = Coinbase_Pro_Websocket(asset_id_cache, channel, log)
            websocket.append_callback(callback)

            self.__websockets[channel][exchange_cache][asset_id_cache] = websocket

            return websocket
        elif exchange_cache == "binance":
            if use_sandbox:
                websocket = Binance_Websocket(asset_id_cache, channel, log,
                                              WEBSOCKET_URL="wss://testnet.binance.vision/ws")
            else:
                websocket = Binance_Websocket(asset_id_cache, channel, log)
            websocket.append_callback(callback)

            self.__websockets[channel][exchange_cache][asset_id_cache] = websocket

            return websocket

    def append_callback(self, callback_object, channel, override_currency=None, override_exchange=None):
        self.websockets = self.__websockets[channel]
        super().append_callback(callback_object, override_currency, override_exchange)

    def is_websocket_open(self, channel, override_currency=None, override_exchange=None):
        self.websockets = self.__websockets[channel]
        return super().is_websocket_open(override_currency, override_exchange)

    def get_most_recent_time(self, channel, override_currency=None, override_exchange=None):
        self.websockets = self.__websockets[channel]
        return super().get_most_recent_time(override_currency, override_exchange)

    def get_time_feed(self, channel, override_currency=None, override_exchange=None):
        self.websockets = self.__websockets[channel]
        return super().get_time_feed(override_currency, override_exchange)

    def get_feed(self, channel, override_currency=None, override_exchange=None):
        self.websockets = self.__websockets[channel]
        return super().get_feed(override_currency, override_exchange)

    def get_response(self, channel, override_currency=None, override_exchange=None):
        self.websockets = self.__websockets[channel]
        return super().get_response(override_currency, override_exchange)

    def close_websocket(self, channel, override_currency=None, override_exchange=None):
        self.websockets = self.__websockets[channel]
        return super().close_websocket(override_currency, override_exchange)

    def restart_ticker(self, channel, override_currency=None, override_exchange=None):
        self.websockets = self.__websockets[channel]
        return super().restart_ticker(override_currency, override_exchange)

    def get_most_recent_tick(self, channel, override_currency=None, override_exchange=None):
        self.websockets = self.__websockets[channel]
        return super().get_most_recent_tick(override_currency, override_exchange)
