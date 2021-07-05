"""
    Alpaca API Interface Definition
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

from alpaca_trade_api.rest import TimeFrame

from Blankly.utils import utils as utils
from Blankly.exchanges.Alpaca.Alpaca_API import API
from Blankly.interface.currency_Interface import CurrencyInterface
import alpaca_trade_api

from Blankly.utils.purchases.limit_order import LimitOrder
from Blankly.utils.purchases.market_order import MarketOrder
from dateutil import parser
import pandas as pd
from datetime import datetime as dt

NY = 'America/New_York'


class AlpacaInterface(CurrencyInterface):
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
            raise LookupError("Alpaca API call failed")

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

        renames = [
            ["symbol", "currency_id"],
        ]
        for i in range(len(assets)):
            assets[i] = utils.rename_to(renames, assets[i])

        for asset in assets:
            base_currency = asset['currency_id']
            asset['currency_id'] += "-USD"
            asset['base_currency'] = base_currency
            asset['quote_currency'] = 'USD'
            asset['base_min_size'] = -1  # TODO: Take a look at this
            asset['base_max_size'] = -1
            asset['base_increment'] = -1

        for i in range(len(assets)):
            assets[i] = utils.isolate_specific(needed, assets[i])

        return assets

    def get_account(self, currency=None):
        assert isinstance(self.calls, alpaca_trade_api.REST)
        needed = self.needed['get_account']

        account_dict = self.calls.get_account()

        positions = self.calls.list_positions()

        positions_dict = utils.AttributeDict({})

        for position in positions:
            symbol = position.pop('symbol')
            if currency is not None and currency == symbol:
                return utils.AttributeDict({
                    'available': position.pop('qty'),
                    'hold': 0  # TODO: Calculate value on hold
                })
            positions_dict[symbol] = utils.AttributeDict({
                'available': position.pop('qty'),
                'hold': 0  # TODO: Calculate value on hold
            })

        for key in positions_dict:
            positions_dict[key] = utils.isolate_specific(needed, positions_dict[key])

        positions_dict.cash = float(account_dict.pop('cash'))

        if currency is not None:
            # if we haven't found the currency, then we'll end up here
            utils.AttributeDict({
                'available': 0,
                'hold': 0
            })
        
        return positions_dict

    def market_order(self, product_id, side, funds) -> MarketOrder:
        assert isinstance(self.calls, alpaca_trade_api.REST)
        needed = self.needed['market_order']

        order = {
            'funds': funds,
            'side': side,
            'product_id': product_id,
            'type': 'market'
        }
        response = self.calls.submit_order(product_id, side=side, type='market', time_in_force='day', notional=funds)
        response['created_at'] = parser.isoparse(response['created_at']).timestamp()
        response = utils.isolate_specific(needed, response)
        return MarketOrder(order, response, self)

    def limit_order(self, product_id: str, side: str, price: float, quantity: int) -> LimitOrder:
        if quantity is not int:
            warnings.warn("Alpaca limit orders must have quantity parameter of type int")
            return

        needed = self.needed['limit_order']

        order = {
            'quantity': quantity,
            'side': side,
            'price': price,
            'product_id': product_id,
            'type': 'limit'
        }
        response = self.calls.submit_order(product_id, side=side, type='limit', time_in_force='day', qty=quantity, limit_price=price)
        response['created_at'] = parser.isoparse(response['created_at']).timestamp()
        response = utils.isolate_specific(needed, response)
        return LimitOrder(order, response, self)

    def cancel_order(self, currency_id, order_id) -> dict:
        assert isinstance(self.calls, alpaca_trade_api.REST)
        self.calls.cancel_order(order_id)

        #TODO: handle the different response codes
        return {'order_id': order_id}

    # TODO: this doesnt exactly fit
    def get_open_orders(self, product_id=None):
        assert isinstance(self.calls, alpaca_trade_api.REST)
        orders = self.calls.list_orders()
        renames = [
            ["asset_id", "product_id"],
            ["filled_at", "price"],
            ["qty", "size"],
            ["notional", "funds"]
        ]
        for order in orders:
            order = utils.rename_to(renames, order)
            needed = self.choose_order_specificity(order['type'])
            order = utils.isolate_specific(needed, order)
        return orders

    def get_order(self, currency_id, order_id) -> dict:
        assert isinstance(self.calls, alpaca_trade_api.REST)
        order = self.calls.get_order(order_id)
        needed = self.choose_order_specificity(order['type'])
        renames = [
            ["asset_id", "product_id"],
            ["filled_at", "price"],
            ["qty", "size"],
            ["notional", "funds"]
        ]
        order = utils.rename_to(renames, order)
        order = utils.isolate_specific(needed, order)
        return order

    def get_fees(self):
        assert isinstance(self.calls, alpaca_trade_api.REST)
        return {
            'maker_fee_rate': 0,
            'taker_fee_rate': 0
        }

    def get_product_history(self, product_id: str, epoch_start: dt, epoch_stop: dt, resolution: int):
        assert isinstance(self.calls, alpaca_trade_api.REST)

        accepted_grans = [1, 60, 3600]
        if resolution not in accepted_grans:
            warnings.warn("Granularity is not an accepted granularity...didnt have a chance to implement more yet, "
                          "returning empty df")
            return pd.DataFrame()

        if resolution == 1:
            time_interval = TimeFrame.Minute
        elif resolution == 60:
            time_interval = TimeFrame.Hour
        else:
            time_interval = TimeFrame.Day

        # '2020-08-28' <- this is how it should look
        formatting_str = "%Y-%m-%d"
        epoch_start_str = epoch_start.strftime(formatting_str)
        epoch_stop_str = epoch_stop.strftime(formatting_str)

        return self.calls.get_bars(product_id, time_interval, epoch_start_str, epoch_stop_str,adjustment='raw').df

    # TODO: tbh not sure how this one works or if it applies to Alpaca
    def get_market_limits(self, product_id):
        assert isinstance(self.calls, alpaca_trade_api.REST)
        pass

    def get_price(self, currency_pair) -> float:
        assert isinstance(self.calls, alpaca_trade_api.REST)
        response = self.calls.get_last_trade(symbol=currency_pair)
        return float(response['price'])