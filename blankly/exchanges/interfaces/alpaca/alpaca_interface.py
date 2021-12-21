"""
    alpaca API Interface Definition
    Copyright (C) 2021  Arun Annamalai, Emerson Dove, Brandon Fan

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
from datetime import datetime as dt, timezone

import alpaca_trade_api
import dateparser
import pandas as pd
from alpaca_trade_api.rest import APIError as AlpacaAPIError, TimeFrame
from dateutil import parser

from blankly.exchanges.interfaces.alpaca.alpaca_api import API
from blankly.exchanges.interfaces.exchange_interface import ExchangeInterface
from blankly.exchanges.orders.limit_order import LimitOrder
from blankly.exchanges.orders.market_order import MarketOrder
from blankly.utils import utils as utils
from blankly.utils.exceptions import APIException
from blankly.utils.time_builder import build_minute, time_interval_to_seconds

NY = 'America/New_York'


class AlpacaInterface(ExchangeInterface):
    def __init__(self, authenticated_api: API, preferences_path: str):
        self.__unique_assets = None
        super().__init__('alpaca', authenticated_api, preferences_path, valid_resolutions=[60, 60*5, 60*15, 60*60*24])
        assert isinstance(self.calls, alpaca_trade_api.REST)

    def init_exchange(self):
        try:
            account_info = self.calls.get_account()
        except alpaca_trade_api.rest.APIError as e:
            raise APIException(e.__str__() + ". Are you trying to use your normal exchange keys "
                               "while in sandbox mode? \nTry toggling the \'use_sandbox\' setting "
                               "in your settings.json or check if the keys were input correctly into your "
                               "keys.json.")
        try:
            if account_info['account_blocked']:
                warnings.warn('Your alpaca account is indicated as blocked for trading....')
        except KeyError:
            raise LookupError("alpaca API call failed")

        filtered_assets = []
        products = self.calls.list_assets(status=None, asset_class=None)
        for i in products:
            if i['symbol'] not in filtered_assets and i['status'] != 'inactive':
                filtered_assets.append(i['symbol'])
            else:
                # TODO handle duplicate symbols
                pass
        self.__unique_assets = filtered_assets

    def get_products(self) -> dict:
        """
        [
            {
              "id": "904837e3-3b76-47ec-b432-046db621571b",
              "class": "us_equity",
              "exchange": "NASDAQ",
              "symbol": "AAPL",
              "status": "active",
              "tradable": true,
              "marginable": true,
              "shortable": true,
              "easy_to_borrow": true,
              "fractionable": true
            },
            ...
        ]
        """
        needed = self.needed['get_products']
        assets = self.calls.list_assets(status=None, asset_class=None)

        for asset in assets:
            base_asset = asset['symbol']
            asset['symbol'] = base_asset
            asset['base_asset'] = base_asset
            asset['quote_asset'] = 'USD'
            if asset['fractionable']:
                asset['base_min_size'] = .000000001
                asset['base_increment'] = .000000001
            else:
                asset['base_min_size'] = 1
                asset['base_increment'] = 1
            asset['base_max_size'] = 10000000000

        for i in range(len(assets)):
            assets[i] = utils.isolate_specific(needed, assets[i])

        return assets

    @property
    def cash(self):
        account_dict = self.calls.get_account()
        return float(account_dict['buying_power'])

    def get_account(self, symbol=None):
        assert isinstance(self.calls, alpaca_trade_api.REST)

        symbol = super().get_account(symbol)

        positions = self.calls.list_positions()
        positions_dict = utils.AttributeDict({})

        for position in positions:
            curr_symbol = position.pop('symbol')
            positions_dict[curr_symbol] = utils.AttributeDict({
                'available': float(position.pop('qty')),
                'hold': 0.0
            })

        symbols = list(positions_dict.keys())
        # Catch an edge case bug that if there are no positions it won't try to snapshot
        if len(symbols) != 0:
            open_orders = self.calls.list_orders(status='open', symbols=symbols)
            snapshot_price = self.calls.get_snapshots(symbols=symbols)
        else:
            open_orders = []
            snapshot_price = {}

        # now grab the available cash in the account
        account = self.calls.get_account()
        positions_dict['USD'] = utils.AttributeDict({
            'available': float(account['buying_power']),
            'hold': 0.0
        })

        for order in open_orders:
            curr_symbol = order['symbol']
            if order['side'] == 'buy':  # buy orders only affect USD holds
                if order['qty']:  # this case handles qty market buy and limit buy
                    if order['type'] == 'limit':
                        dollar_amt = float(order['qty']) * float(order['limit_price'])
                    elif order['type'] == 'market':
                        dollar_amt = float(order['qty']) * snapshot_price[curr_symbol]['latestTrade']['p']
                    else:  # we don't have support for stop_order, stop_limit_order
                        dollar_amt = 0.0
                else:  # this is the case for notional market buy
                    dollar_amt = float(order['notional'])

                # In this case we don't have to subtract because the buying power is the available money already
                # we just need to add to figure out how much is actually on limits
                # positions_dict['USD']['available'] -= dollar_amt

                # So just add to our hold
                positions_dict['USD']['hold'] += dollar_amt

            else:
                if order['qty']:  # this case handles qty market sell and limit sell
                    qty = float(order['qty'])
                else:  # this is the case for notional market sell, calculate the qty with cash/price
                    qty = float(order['notional']) / snapshot_price[curr_symbol]['latestTrade']['p']

                positions_dict[curr_symbol]['available'] -= qty
                positions_dict[curr_symbol]['hold'] += qty

        # Note that now __unique assets could be uninitialized:
        if self.__unique_assets is None:
            self.init_exchange()

        for i in self.__unique_assets:
            if i not in positions_dict:
                positions_dict[i] = utils.AttributeDict({
                    'available': 0.0,
                    'hold': 0.0
                })

        if symbol is not None:
            if symbol in positions_dict:
                return utils.AttributeDict({
                    'available': float(positions_dict[symbol]['available']),
                    'hold': float(positions_dict[symbol]['hold'])
                })
            else:
                raise KeyError('Symbol not found.')

        if symbol == 'USD':
            return utils.AttributeDict({
                'available': positions_dict['USD']['available'],
                'hold': positions_dict['USD']['hold']
            })

        return positions_dict

    @utils.order_protection
    def market_order(self, symbol, side, size) -> MarketOrder:
        assert isinstance(self.calls, alpaca_trade_api.REST)
        needed = self.needed['market_order']

        renames = [
            ['qty', 'size']
        ]

        order = {
            'size': size,
            'side': side,
            'symbol': symbol,
            'type': 'market'
        }
        response = self.calls.submit_order(symbol, side=side, type='market', time_in_force='day', qty=size)
        response['created_at'] = parser.isoparse(response['created_at']).timestamp()
        response = utils.rename_to(renames, response)
        response = utils.isolate_specific(needed, response)
        return MarketOrder(order, response, self)

    @utils.order_protection
    def limit_order(self, symbol: str, side: str, price: float, size: float) -> LimitOrder:
        needed = self.needed['limit_order']

        renames = [
            ['limit_price', 'price'],
            ['qty', 'size']
        ]

        order = {
            'quantity': size,
            'side': side,
            'price': price,
            'symbol': symbol,
            'type': 'limit'
        }
        response = self.calls.submit_order(symbol,
                                           side=side,
                                           type='limit',
                                           time_in_force='gtc',
                                           qty=size,
                                           limit_price=price)

        response['created_at'] = parser.isoparse(response['created_at']).timestamp()
        response = utils.rename_to(renames, response)
        response = utils.isolate_specific(needed, response)
        response['time_in_force'] = response['time_in_force'].upper()
        return LimitOrder(order, response, self)

    def cancel_order(self, symbol, order_id) -> dict:
        assert isinstance(self.calls, alpaca_trade_api.REST)
        self.calls.cancel_order(order_id)

        # TODO: handle the different response codes
        return {'order_id': order_id}

    def get_open_orders(self, symbol=None):
        assert isinstance(self.calls, alpaca_trade_api.REST)
        if symbol is None:
            orders = self.calls.list_orders(status='open')
        else:
            orders = self.calls.list_orders(status='open', symbols=[symbol])

        for i in range(len(orders)):
            # orders[i] = utils.rename_to(renames, orders[i])
            # if orders[i]['type'] == "limit":
            #     orders[i]['price'] = orders[i]['limit_price']
            # if orders[i]['type'] == "market":
            #     if orders[i]['notional']:
            #         orders[i]['funds'] = orders[i]['notional']
            #     else:
            #         orders[i]['funds'] = orders[i]['notional']
            # orders[i]['created_at'] = parser.isoparse(orders[i]['created_at']).timestamp()
            orders[i] = self.homogenize_order(orders[i])

        return orders

    def get_order(self, symbol, order_id) -> dict:
        assert isinstance(self.calls, alpaca_trade_api.REST)
        order = self.calls.get_order(order_id)
        order = self.homogenize_order(order)
        return order

    # TODO: fix this function
    def homogenize_order(self, order):
        if order['type'] == "limit":
            renames = [
                ["qty", "size"],
                ["limit_price", "price"]
            ]
            order = utils.rename_to(renames, order)

        elif order['type'] == "market":
            if order['notional']:
                renames = [
                    ["notional", "funds"]
                ]
                order = utils.rename_to(renames, order)

            else:  # market order of number of shares
                order['size'] = order.pop('qty')

        # TODO: test stop_limit orders
        elif order['type'] == "stop_limit":
            renames = [
                ["qty", "size"],
            ]
            order = utils.rename_to(renames, order)

        order['created_at'] = parser.isoparse(order['created_at']).timestamp()
        needed = self.choose_order_specificity(order['type'])

        order = utils.isolate_specific(needed, order)
        return order

    def get_fees(self):
        assert isinstance(self.calls, alpaca_trade_api.REST)
        return {
            'maker_fee_rate': 0.0,
            'taker_fee_rate': 0.0
        }

    def get_product_history(self, symbol: str, epoch_start: float, epoch_stop: float, resolution: int):
        assert isinstance(self.calls, alpaca_trade_api.REST)

        resolution = time_interval_to_seconds(resolution)

        supported_multiples = [60, 3600, 86400]
        if resolution not in supported_multiples:
            utils.info_print("Granularity is not an accepted granularity...rounding to nearest valid value.")
            resolution = supported_multiples[min(range(len(supported_multiples)),
                                             key=lambda i: abs(supported_multiples[i] - resolution))]

        found_multiple, row_divisor = super().evaluate_multiples(supported_multiples, resolution)

        if found_multiple == 60:
            time_interval = TimeFrame.Minute
        elif found_multiple == 3600:
            time_interval = TimeFrame.Hour
        else:
            time_interval = TimeFrame.Day

        epoch_start_str = dt.fromtimestamp(epoch_start, tz=timezone.utc).isoformat()
        epoch_stop_str = dt.fromtimestamp(epoch_stop, tz=timezone.utc).isoformat()

        try:
            try:
                bars = self.calls.get_bars(symbol, time_interval, epoch_start_str, epoch_stop_str, adjustment='raw').df
            except TypeError:
                # If you query a timeframe with no data the API throws a Nonetype issue so just return something
                #  empty if that happens
                return pd.DataFrame(columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        except AlpacaAPIError as e:
            if e.code == 42210000:
                warning_string = "Your alpaca subscription does not permit querying data from the last 15 minutes. " \
                                 "Blankly is adjusting your query."
                utils.info_print(warning_string)
                epoch_stop = time.time() - (build_minute() * 15)
                if epoch_stop >= epoch_start:
                    try:
                        return self.get_product_history(symbol, epoch_start, epoch_stop, resolution)
                    except TypeError:
                        # If you query a timeframe with no data the API throws a Nonetype issue so just return something
                        #  empty if that happens
                        return pd.DataFrame(columns=['time', 'open', 'high', 'low', 'close', 'volume'])
                else:
                    warning_string = "No data range queried after time adjustment."
                    utils.info_print(warning_string)
                    return pd.DataFrame(columns=['time', 'open', 'high', 'low', 'close', 'volume'])
            else:
                raise e
        bars.rename(columns={"t": "time", "o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"},
                    inplace=True)

        if bars.empty:
            return pd.DataFrame(columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        return utils.get_ohlcv(bars, row_divisor, from_zero=False)

    # def history(self,
    #             symbol: str,
    #             to: Union[str, int] = 200,
    #             resolution: Union[str, int] = '1d',
    #             start_date: Union[str, dt, float] = None,
    #             end_date: Union[str, dt, float] = None,
    #             return_as: str = 'df'):
    #
    #     assert isinstance(self.calls, alpaca_trade_api.REST)
    #
    #     if not end_date:
    #         end_date = dt.now(tz=timezone.utc)
    #
    #     end_date = self.__convert_times(end_date)
    #
    #     if start_date:
    #         start_date = self.__convert_times(start_date)
    #
    #     alpaca_v1_resolutions = [60 * 1, 60 * 5, 60 * 15, 60 * 60 * 24]
    #
    #     # convert resolution into epoch seconds
    #     resolution_seconds = time_interval_to_seconds(resolution)
    #
    #     found_multiple, row_divisor = self.__evaluate_multiples(alpaca_v1_resolutions, resolution_seconds)
    #
    #     if found_multiple == 60:
    #         time_interval = '1Min'
    #     elif found_multiple == 60 * 5:
    #         time_interval = '5Min'
    #     elif found_multiple == 60 * 15:
    #         time_interval = '15Min'
    #     elif found_multiple == 60 * 60 * 24:
    #         time_interval = '1D'
    #     else:
    #         time_interval = 'failed'
    #
    #     if to:
    #         aggregated_limit = to * row_divisor
    #         bars = self.calls.get_barset(symbol, time_interval, limit=int(aggregated_limit),
    #         end=end_date.isoformat())[
    #             symbol]
    #         return_df = pd.DataFrame(bars)
    #         return_df.rename(columns={"t": "time", "o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"},
    #                          inplace=True)
    #
    #         history = utils.get_ohlcv(return_df, row_divisor, from_zero=True)
    #
    #     else:
    #         # bars = self.calls.get_barset(symbol, time_interval, start=start_date.isoformat(),
    #         # end=end_date.isoformat())[symbol]
    #         history = self.get_product_history(symbol,
    #                                            start_date.timestamp(),
    #                                            end_date.timestamp(),
    #                                            int(resolution_seconds))
    #
    #     return super().cast_type(history, return_as)
    #     # return_df = pd.DataFrame(bars)
    #     # return_df.rename(columns={"t": "time", "o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"},
    #     # inplace=True)
    #     #
    #     # return utils.get_ohlcv_2(return_df, row_divisor)

    def overridden_history(self, symbol, epoch_start, epoch_stop, resolution_seconds, **kwargs) -> pd.DataFrame:
        to = kwargs['to']
        # If it's a string alpaca is an edge case where epoch can be used
        if to is not None and isinstance(to, str):
            to = None
        if to:
            resolution_seconds = self.valid_resolutions[min(range(len(self.valid_resolutions)),
                                                            key=lambda j: abs(self.valid_resolutions[j] -
                                                                              resolution_seconds))]
            resolution_lookup = {
                60: '1Min',
                300: '5Min',
                900: '15Min',
                86400: '1D'
            }
            time_interval = resolution_lookup[resolution_seconds]

            frames = []

            while to > 1000:
                # Create an end time by moving after the start time by 1000 datapoints
                epoch_start += resolution_seconds * 1000

                frames.append(self.calls.get_barset(symbol, time_interval, limit=1000,
                                                    end=utils.ISO8601_from_epoch(epoch_start))[symbol])
                to -= 1000

            frames.append(self.calls.get_barset(symbol, time_interval, limit=to,
                                                end=utils.ISO8601_from_epoch(epoch_stop))[symbol])

            for i in range(len(frames)):
                frames[i] = pd.DataFrame(frames[i])

            response = pd.concat(frames, ignore_index=True)
            response.rename(columns={"t": "time", "o": "open", "h": "high", "l": "low", "c": "close", "v":
                            "volume"}, inplace=True)

            response = response.astype({
                'time': int,
                'open': float,
                'high': float,
                'low': float,
                'close': float,
                'volume': float,
            })
        else:
            response = self.get_product_history(symbol,
                                                epoch_start,
                                                epoch_stop,
                                                int(resolution_seconds))

        return response

    @staticmethod
    def __convert_times(date):  # There aren't any usages of this
        # convert start_date to datetime object
        if isinstance(date, str):
            date = dateparser.parse(date)
        elif isinstance(date, float):
            date = dt.fromtimestamp(date)

        # end_date object is naive datetime, so need to convert
        if date.tzinfo is None or date.tzinfo.utcoffset(date) is None:
            date = date.replace(tzinfo=timezone.utc)

        return date

    def get_order_filter(self, symbol: str):
        assert isinstance(self.calls, alpaca_trade_api.REST)
        current_price = self.get_price(symbol)

        products = self.get_products()

        product = None
        for i in products:
            if i['symbol'] == symbol:
                product = i
                break
        if product is None:
            raise APIException("Symbol not found.")

        exchange_specific = product['exchange_specific']
        fractionable = exchange_specific['fractionable']

        if fractionable:
            quote_increment = 1e-9
            min_funds_buy = 1
            min_funds_sell = 1e-9 * current_price

            # base_min_size = product['base_min_size']
            base_max_size = product['base_max_size']
            # base_increment = product['base_increment']
            min_price = 0.0001
            max_price = 10000000000
        else:
            quote_increment = current_price
            min_funds_buy = current_price
            min_funds_sell = current_price

            # base_min_size = product['base_min_size']
            base_max_size = product['base_max_size']
            # base_increment = product['base_increment']
            min_price = 0.0001
            max_price = 10000000000

        max_funds = current_price * 10000000000

        return {
            "symbol": symbol,
            "base_asset": symbol,
            "quote_asset": 'USD',
            "max_orders": 500,  # More than this and we can't calculate account value (alpaca is very bad)
            "limit_order": {
                "base_min_size": 1,  # Minimum size to buy
                "base_max_size": base_max_size,  # Maximum size to buy
                "base_increment": 1,  # Specifies the minimum increment for the base_asset.

                "price_increment": min_price,  # TODO test this at market open

                "min_price": min_price,
                "max_price": max_price,
            },
            'market_order': {
                "fractionable": fractionable,

                # TODO alpaca is very broken right now and is only allowing whole number quantity so these are
                #  overridden. If I see anyone creating an issue about this it better be that I can finally allow
                #  fractional back
                "base_min_size": 1,  # Minimum size to buy
                "base_max_size": base_max_size,  # Maximum size to buy
                "base_increment": 1,  # Specifies the minimum increment for the base_asset.

                "quote_increment": quote_increment,  # Specifies the min order price as well as the price increment.
                "buy": {
                    "min_funds": min_funds_buy,
                    "max_funds": max_funds,
                },
                "sell": {
                    "min_funds": min_funds_sell,
                    "max_funds": max_funds,
                },
            },
            "exchange_specific": {
                "id": exchange_specific['id'],
                "class": exchange_specific['class'],
                "exchange": exchange_specific['exchange'],
                "status": exchange_specific['status'],
                "tradable": exchange_specific['tradable'],
                "marginable": exchange_specific['marginable'],
                "shortable": exchange_specific['shortable'],
                "easy_to_borrow": exchange_specific['easy_to_borrow'],
                "price": current_price
            }
        }

    def get_price(self, symbol) -> float:
        assert isinstance(self.calls, alpaca_trade_api.REST)
        response = self.calls.get_last_trade(symbol=symbol)
        return float(response['price'])
