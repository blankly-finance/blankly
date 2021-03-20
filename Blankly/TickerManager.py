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


from Blankly.Coinbase_Pro.Coinbase_Pro_Tickers import Tickers as Coinbase_Pro_Ticker


class TickerManager:
    def __init__(self, exchange_name):
        self.__exchange_name = exchange_name
        self.__tickers = {
            "coinbase_pro": {

            }
        }

    def create_ticker(self, currency_id, callback, log='', override_exchange=None):
        """
        Create a ticker on the
        """
        exchange_name = self.__exchange_name
        if override_exchange is not None:
            exchange_name = override_exchange

        if exchange_name == "coinbase_pro":
            ticker = Coinbase_Pro_Ticker(currency_id, log=log)
            ticker.append_callback(callback)
            # Store this object
            self.__tickers['coinbase_pro'][currency_id] = ticker
            return ticker

    def append_callback(self, currency_id, callback_object, override_callback_name=None, override_exchange=None):
        """
        Add another object to have the price_event() function called.
        Generally the callback object should be "self" and the callback_name should only be filled if you want to
        override the default "price_event()" function call.
        This can be very useful in working with multiple tickers, but not necessary on a simple bot.
        """
        exchange_name = self.__exchange_name
        if override_exchange is not None:
            exchange_name = override_exchange

        if exchange_name == "coinbase_pro":
            self.__tickers['coinbase_pro'][currency_id].append_callback(callback_object)
