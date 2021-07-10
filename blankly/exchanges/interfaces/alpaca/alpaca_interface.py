"""
    alpaca API Interface Definition
    Copyright (C) 2021  Arun Annamalai

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


import warnings

import pytz
from alpaca_trade_api.rest import TimeFrame

from blankly.utils import utils as utils
from blankly.exchanges.interfaces.alpaca.alpaca_api import API
from blankly.exchanges.interfaces.exchange_interface import ExchangeInterface
import alpaca_trade_api

from blankly.exchanges.orders.limit_order import LimitOrder
from blankly.exchanges.orders.market_order import MarketOrder
from dateutil import parser
from datetime import datetime as dt

from blankly.utils.time import is_datetime_naive

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
            asset['symbol'] += "-USD"
            asset['base_asset'] = base_asset
            asset['quote_asset'] = 'USD'
            asset['base_min_size'] = -1  # TODO: Take a look at this
            asset['base_max_size'] = -1
            asset['base_increment'] = -1

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

        account_dict = self.calls.get_account()

        positions = self.calls.list_positions()

        positions_dict = utils.AttributeDict({})

        for position in positions:
            curr_symbol = position.pop('symbol')
            if symbol is not None and curr_symbol == symbol:
                return utils.AttributeDict({
                    'available': position.pop('qty'),
                    'hold': 0  # TODO: Calculate value on hold
                })
            positions_dict[curr_symbol] = utils.AttributeDict({
                'available': position.pop('qty'),
                'hold': 0  # TODO: Calculate value on hold
            })

        for key in positions_dict:
            positions_dict[key] = utils.isolate_specific(needed, positions_dict[key])

        if symbol is not None:
            # if we haven't found the currency, then we'll end up here
            utils.AttributeDict({
                'available': 0,
                'hold': 0
            })
        
        return positions_dict

    def market_order(self, symbol, side, funds) -> MarketOrder:
        assert isinstance(self.calls, alpaca_trade_api.REST)
        needed = self.needed['market_order']

        order = {
            'funds': funds,
            'side': side,
            'symbol': symbol,
            'type': 'market'
        }
        response = self.calls.submit_order(symbol, side=side, type='market', time_in_force='day', notional=funds)
        response['created_at'] = parser.isoparse(response['created_at']).timestamp()
        response = utils.isolate_specific(needed, response)
        return MarketOrder(order, response, self)

    def limit_order(self, symbol: str, side: str, price: float, quantity: int) -> LimitOrder:
        needed = self.needed['limit_order']

        order = {
            'quantity': quantity,
            'side': side,
            'price': price,
            'symbol': symbol,
            'type': 'limit'
        }
        response = self.calls.submit_order(symbol, side=side, type='limit', time_in_force='gtc', qty=quantity, limit_price=price)
        response['created_at'] = parser.isoparse(response['created_at']).timestamp()
        response = utils.isolate_specific(needed, response)
        return LimitOrder(order, response, self)

    def cancel_order(self, symbol, order_id) -> dict:
        assert isinstance(self.calls, alpaca_trade_api.REST)
        self.calls.cancel_order(order_id)

        #TODO: handle the different response codes
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
            'maker_fee_rate': 0,
            'taker_fee_rate': 0
        }

    def get_product_history(self, symbol: str, epoch_start: int, epoch_stop: int, resolution: int):
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
            raise ValueError("alpaca currently does not support this specific resolution, please make the resolution a multiple of 1 minute, 1 hour or 1 day")
        
        row_divisor = resolution // multiple

        if row_divisor > 100:
            raise Warning("The resolution you requested is an extremely high of the base resolutions supported and may slow down the performance of your model: {} * {}"
                .format(found_multiple, row_divisor))

        if found_multiple == 60:
            time_interval = TimeFrame.Minute
        elif found_multiple == 3600:
            time_interval = TimeFrame.Hour
        else:
            time_interval = TimeFrame.Day


        epoch_start_str = dt.utcfromtimestamp(epoch_start).isoformat()
        epoch_stop_str = dt.utcfromtimestamp(epoch_stop).isoformat()
        bars = self.calls.get_bars(symbol, time_interval, epoch_start_str, epoch_stop_str, adjustment='raw').df
        bars.rename(columns={"o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"})
        return utils.get_ohlcv(bars, row_divisor)

    # TODO: tbh not sure how this one works or if it applies to alpaca
    def get_asset_limits(self, symbol: str):
        assert isinstance(self.calls, alpaca_trade_api.REST)
        pass

    def get_price(self, symbol) -> float:
        assert isinstance(self.calls, alpaca_trade_api.REST)
        response = self.calls.get_last_trade(symbol=symbol)
        return float(response['price'])
