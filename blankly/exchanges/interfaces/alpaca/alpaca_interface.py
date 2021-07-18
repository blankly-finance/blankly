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
from typing import Union

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
    def __init__(self, authenticated_API: API, preferences_path: str):
        super().__init__('alpaca', authenticated_API, preferences_path)
        assert isinstance(self.calls, alpaca_trade_api.REST)

    def init_exchange(self):
        assert isinstance(self.calls, alpaca_trade_api.REST)
        account_info = self.calls.get_account()
        try:
            if account_info['account_blocked']:
                warnings.warn('Your alpaca account is indicated as blocked for trading....')
        except KeyError:
            raise LookupError("alpaca API call failed")

        self.__exchange_properties = {
            "maker_fee_rate": 0,
            "taker_fee_rate": 0
        }

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
        needed = self.needed['get_account']

        positions = self.calls.list_positions()
        positions_dict = utils.AttributeDict({})

        for position in positions:
            curr_symbol = position.pop('symbol')
            positions_dict[curr_symbol] = utils.AttributeDict({
                'available': float(position.pop('qty')),
                'hold': 0
            })

        symbols = positions_dict.keys()
        open_orders = self.calls.list_orders(symbols=symbols)
        snapshot_price = self.calls.get_snapshots(symbols=symbols)

        # now grab the available cash in the account
        account = self.calls.get_account()
        positions_dict['USD'] = utils.AttributeDict({
            'available': float(account['cash']),
            'hold': 0
        })

        for order in open_orders:
            if order['side'] == 'buy':  # buy orders only affect USD holds
                if order['qty']:  # this case handles qty market buy and limit buy
                    if order['type'] == 'limit':
                        dollar_amt = float(order['qty']) * float(order['limit_price'])
                    elif order['type'] == 'market':
                        dollar_amt = float(order['qty']) * snapshot_price[curr_symbol]['latestTrade']['p']
                    else: # we dont have support for stop_order, stop_limit_order
                        dollar_amt = 0
                else:  # this is the case for notional market buy
                    dollar_amt = order['notional']

                positions_dict['USD']['available'] -= dollar_amt
                positions_dict['USD']['hold'] += dollar_amt

            else:
                curr_symbol = order['symbol']
                if order['qty']:  # this case handles qty market sell and limit sell
                    qty = float(order['qty'])
                else:  # this is the case for notional market sell, calculate the qty with cash/price
                    qty = float(order['notional']) / snapshot_price[curr_symbol]['latestTrade']['p']

                positions_dict[curr_symbol]['available'] -= qty
                positions_dict[curr_symbol]['hold'] += qty

                if symbol is not None and curr_symbol == symbol:
                    return utils.AttributeDict({
                        'available': positions_dict[curr_symbol]['available'],
                        'hold': positions_dict[curr_symbol]['hold']
                    })

        if symbol == 'USD':
            return utils.AttributeDict({
                'available': positions_dict['USD']['available'],
                'hold': positions_dict['USD']['available']
            })

        if symbol is not None:
            # if we haven't found the currency, then we'll end up here
            return utils.AttributeDict({
                'available': 0,
                'hold': 0
            })

        for key in positions_dict:
            positions_dict[key] = utils.isolate_specific(needed, positions_dict[key])

        return positions_dict

    def market_order(self, symbol, side, funds) -> MarketOrder:
        assert isinstance(self.calls, alpaca_trade_api.REST)
        needed = self.needed['market_order']

        renames = [
            ['notional', 'funds']
        ]

        order = {
            'funds': funds,
            'side': side,
            'symbol': symbol,
            'type': 'market'
        }
        response = self.calls.submit_order(symbol, side=side, type='market', time_in_force='day', notional=funds)
        response['created_at'] = parser.isoparse(response['created_at']).timestamp()
        response = utils.rename_to(renames, response)
        response = utils.isolate_specific(needed, response)
        return MarketOrder(order, response, self)

    def limit_order(self, symbol: str, side: str, price: float, quantity: int) -> LimitOrder:
        needed = self.needed['limit_order']

        renames = [
            ['limit_price', 'price'],
            ['qty', 'size']
        ]

        order = {
            'quantity': quantity,
            'side': side,
            'price': price,
            'symbol': symbol,
            'type': 'limit'
        }
        response = self.calls.submit_order(symbol,
                                           side=side,
                                           type='limit',
                                           time_in_force='gtc',
                                           qty=quantity,
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

    # TODO: this doesnt exactly fit
    def get_open_orders(self, symbol=None):
        assert isinstance(self.calls, alpaca_trade_api.REST)
        orders = self.calls.list_orders()
        renames = [
            ["asset_id", "symbol"],
            ["filled_avg_price", "price"],
            ["qty", "size"],
            ["notional", "funds"]
        ]
        for order in orders:
            order = utils.rename_to(renames, order)
            needed = self.choose_order_specificity(order['type'])
            order['created_at'] = parser.isoparse(order['created_at']).timestamp()
            order = utils.isolate_specific(needed, order)
        return orders

    def get_order(self, symbol, order_id) -> dict:
        assert isinstance(self.calls, alpaca_trade_api.REST)
        order = self.calls.get_order(order_id)
        needed = self.choose_order_specificity(order['type'])
        renames = [
            ["asset_id", "symbol"],
            ["filled_avg_price", "price"],
            ["qty", "size"],
            ["notional", "funds"]
        ]
        order = utils.rename_to(renames, order)
        order['created_at'] = parser.isoparse(order['created_at']).timestamp()
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

        supported_multiples = [60, 3600, 86400]
        if resolution < 60:
            raise ValueError("alpaca does not support sub-minute candlesticks")

        found_multiple = -1
        for multiple in reversed(supported_multiples):
            if resolution % multiple == 0:
                found_multiple = multiple
                break
        if found_multiple < 0:
            raise ValueError("alpaca currently does not support this specific resolution, please make the resolution a "
                             "multiple of 1 minute, 1 hour or 1 day")

        row_divisor = resolution / found_multiple
        row_divisor = int(row_divisor)

        if row_divisor > 100:
            raise Warning("The resolution you requested is an extremely high of the base resolutions supported and may "
                          "slow down the performance of your model: {} * {}".format(found_multiple, row_divisor))

        if found_multiple == 60:
            time_interval = TimeFrame.Minute
        elif found_multiple == 3600:
            time_interval = TimeFrame.Hour
        else:
            time_interval = TimeFrame.Day

        epoch_start_str = dt.fromtimestamp(epoch_start, tz=timezone.utc).isoformat()
        epoch_stop_str = dt.fromtimestamp(epoch_stop, tz=timezone.utc).isoformat()

        try:
            bars = self.calls.get_bars(symbol, time_interval, epoch_start_str, epoch_stop_str, adjustment='raw').df
        except AlpacaAPIError as e:
            if e.code == 42210000:
                warning_string = "Your alpaca subscription does not permit querying data from the last 15 minutes. " \
                                 "Blankly is adjusting your query."
                warnings.warn(warning_string)
                epoch_stop = time.time() - (build_minute() * 15)
                if epoch_stop >= epoch_start:
                    return self.get_product_history(symbol, epoch_start, epoch_stop, resolution)
                else:
                    warning_string = "No data range queried after time adjustmnet."
                    warnings.warn(warning_string)
                    return pd.DataFrame(columns=['time', 'open', 'high', 'low', 'close', 'volume'])
            else:
                raise e
        bars.rename(columns={"t": "time", "o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"},
                    inplace=True)

        return utils.get_ohlcv(bars, row_divisor)

    def history(self,
                symbol: str,
                to: Union[str, int] = None,
                resolution: Union[str, float] = '1d',
                start_date: Union[str, dt, float] = None,
                end_date: Union[str, dt, float] = None):

        assert isinstance(self.calls, alpaca_trade_api.REST)
        if not to and not start_date:
            raise ValueError("history() call needs only 1 of {start_date, to} defined")
        if to and start_date:
            raise ValueError("history() call needs only 1 of {start_date, to} defined")

        if not end_date:
            end_date = dt.now(tz=timezone.utc)

        # convert end_date to datetime object
        if isinstance(end_date, str):
            end_date = dateparser.parse(end_date)
        elif isinstance(end_date, float):
            end_date = dt.fromtimestamp(end_date)

        # end_date object is naive datetime, so need to convert
        if end_date.tzinfo is None or end_date.tzinfo.utcoffset(end_date) is None:
            end_date = end_date.replace(tzinfo=timezone.utc)

        if start_date:
            # convert start_date to datetime object
            if isinstance(start_date, str):
                start_date = dateparser.parse(start_date)
            elif isinstance(start_date, float):
                start_date = dt.fromtimestamp(start_date)

            # end_date object is naive datetime, so need to convert
            if start_date.tzinfo is None or start_date.tzinfo.utcoffset(start_date) is None:
                start_date = start_date.replace(tzinfo=timezone.utc)

        alpaca_v1_resolutions = [60 * 1, 60 * 5, 60 * 15, 60 * 60 * 24]

        # convert resolution into epoch seconds
        resolution_seconds = time_interval_to_seconds(resolution)

        found_multiple = -1
        for multiple in reversed(alpaca_v1_resolutions):
            if resolution_seconds % multiple == 0:
                found_multiple = multiple
                break
        if found_multiple < 0:
            raise ValueError("alpaca currently does not support this specific resolution, please make the resolution a "
                             "multiple of 1 minute, 1 hour or 1 day")

        row_divisor = resolution_seconds / found_multiple
        row_divisor = int(row_divisor)

        if row_divisor > 100:
            raise Warning("The resolution you requested is an extremely high of the base resolutions supported and may "
                          "slow down the performance of your model: {} * {}".format(found_multiple, row_divisor))

        if found_multiple == 60:
            time_interval = '1Min'
        elif found_multiple == 60 * 5:
            time_interval = '5Min'
        elif found_multiple == 60 * 15:
            time_interval = '15Min'
        elif found_multiple == 60 * 60 * 24:
            time_interval = '1D'

        if to:
            aggregated_limit = to * row_divisor
            bars = self.calls.get_barset(symbol, time_interval, limit=int(aggregated_limit), end=end_date.isoformat())[
                symbol]
            return_df = pd.DataFrame(bars)
            return_df.rename(columns={"t": "time", "o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"},
                             inplace=True)

            return utils.get_ohlcv_2(return_df, row_divisor)
        else:
            # bars = self.calls.get_barset(symbol, time_interval, start=start_date.isoformat(), end=end_date.isoformat())[symbol]
            return self.get_product_history(symbol, start_date.timestamp(), end_date.timestamp(), resolution_seconds)
        # return_df = pd.DataFrame(bars)
        # return_df.rename(columns={"t": "time", "o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"}, inplace=True)
        #
        # return utils.get_ohlcv_2(return_df, row_divisor)

    # TODO: tbh not sure how this one works or if it applies to alpaca
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
