"""
    Logic to provide consistency across exchanges
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

import time
import warnings
import pandas as pd
import datetime

import Blankly.Utils
from Blankly.Purchase import Purchase


class APIInterface:
    def __init__(self, exchange_name, authenticated_API, exchange_properties, user_preferences):
        self.__exchange_name = exchange_name
        self.__calls = authenticated_API
        self.__ticker_manager = None
        self.__exchange_properties = exchange_properties
        self.__user_preferences = user_preferences
        self.__paper_trading = self.__user_preferences["settings"]["paper_trade"]

    def get_calls(self):
        return self.__calls

    """
    Get all currencies in an account
    """
    def get_account(self, account_id=None):
        if self.__exchange_name == "coinbase_pro":
            if account_id is None:
                return self.__calls.get_accounts()
            else:
                return self.__calls.get_account(account_id)

    def market_order(self, product_id, side, funds, kwargs):
        """
        Used for buying or selling market orders
        Args:
            product_id: currency to buy
            side: buy/sell
            funds: desired amount of quote currency to use
            kwargs: specific arguments that may be used by each exchange, if exchange is known
        """
        if self.__exchange_name == "coinbase_pro":
            order = {
                'funds': funds,
                'side': side,
                'product_id': product_id,
            }
            response = self.__calls.place_market_order(product_id, side, funds, **kwargs)
            return Purchase(order,
                            response,
                            self.__ticker_manager.get_ticker(product_id, override_default_exchange_name="coinbase_pro"),
                            self.__exchange_properties)

    def limit_order(self, product_id, side, price, size, kwargs):
        """
        Used for buying or selling limit orders
        Args:
            product_id: currency to buy
            side: buy/sell
            price: price to set limit order
            size: amount of currency (like BTC) for the limit to be valued
            kwargs: specific arguments that may be used by each exchange, (if exchange is known)
        """
        if self.__exchange_name == "coinbase_pro":
            # order = Coinbase_Pro_Utils.CoinbaseProUtils().generate_limit_order(size, price, side, id)
            order = {
                'size': size,
                'side': side,
                'product_id': product_id,
            }
            self.__calls.placeOrder(product_id, side, price, size)
            response = self.__calls.place_market_order(product_id, side, price, size, **kwargs)
            return Purchase(order,
                            response,
                            self.__ticker_manager.get_ticker(product_id, override_default_exchange_name="coinbase_pro"),
                            self.__exchange_properties)

    def stop_order(self, product_id, side, price, size=None, funds=None):
        """

        """
        pass

    def get_fees(self):
        if self.__exchange_name == "coinbase_pro":
            return self.__calls.get_fees()

    def get_products(self):
        if self.__exchange_name == "coinbase_pro":
            return self.__calls.get_products()

    def get_product_history(self, product_id, epoch_start, epoch_stop, granularity):
        if self.__exchange_name == "coinbase_pro":
            accepted_grans = [60, 300, 900, 3600, 21600, 86400]
            if granularity not in accepted_grans:
                warnings.warn("Granularity is not in accepted granularity...rounding down.")
                if granularity < 60:
                    granularity = 60
                elif granularity < 300:
                    granularity = 60
                elif granularity < 900:
                    granularity = 300
                elif granularity < 3600:
                    granularity = 900
                elif granularity < 21600:
                    granularity = 3600
                elif granularity < 86400:
                    granularity = 21600
                else:
                    granularity = 86400

            # Figure out how many points are needed
            need = int((epoch_stop - epoch_start) / granularity)
            window_open = epoch_start
            history = []
            # Iterate while its more than max
            while need > 300:
                # Close is always 300 points ahead
                window_close = window_open + 300 * granularity
                open_iso = Blankly.Utils.ISO8601_from_epoch(window_open)
                close_iso = Blankly.Utils.ISO8601_from_epoch(window_close)
                # output = self.__calls.get_product_historic_rates(product_id, open_iso, close_iso, granularity)
                history = history + self.__calls.get_product_historic_rates(product_id, open_iso, close_iso,
                                                                            granularity)

                window_open = window_close
                need -= 300
                time.sleep(1)

            # Fill the remainder
            open_iso = Blankly.Utils.ISO8601_from_epoch(window_open)
            close_iso = Blankly.Utils.ISO8601_from_epoch(epoch_stop)
            history_block = history + self.__calls.get_product_historic_rates(product_id, open_iso, close_iso,
                                                                              granularity)
            return pd.DataFrame(history_block, columns=['time', 'low', 'high', 'open', 'close', 'volume'])

    # def create_ticker(self, callback, currency_id, log=''):
    #     """
    #     Creates ticker connection.
    #     """
    #     if self.__exchange_name == "coinbase_pro":
    #         ticker = Coinbase_Pro_Ticker(currency_id, log=log)
    #         ticker.append_callback(callback)
    #         return ticker

    def append_ticker_manager(self, ticker_manager):
        self.__ticker_manager = ticker_manager
