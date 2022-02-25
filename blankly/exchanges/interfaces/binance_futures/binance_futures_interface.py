"""
    Binance Futures ExchangeInterface object.
    Copyright (C) 2022 Matias Kotlik

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

import binance.error
import pandas as pd
from binance.client import Client

import blankly
import blankly.utils.exceptions as exceptions
import blankly.utils.utils as utils
from blankly.exchanges.interfaces.futures_exchange_interface import FuturesExchangeInterface
from blankly.exchanges.orders.futures.futures_limit_order import FuturesLimitOrder
from blankly.exchanges.orders.futures.futures_market_order import FuturesMarketOrder


class BinanceFuturesInterface(FuturesExchangeInterface):
    calls: Client
    available_currencies: list

    def __init__(self, exchange_name, authenticated_api):
        super().__init__(exchange_name, authenticated_api)

    def init_exchange(self):
        try:
            self.calls.futures_account()
        except binance.error.ClientError as e:
            raise exceptions.APIException(
                f"{e.error_message}. Are you trying to use your normal exchange keys while in sandbox mode? \nTry "
                "toggling the 'use_sandbox' setting in your settings.json or check if the keys were input "
                "correctly into your keys.json.")

        # TODO allow hedge mode
        # if self.calls.futures_get_position_mode()['dualSidePosition']:
        #     self.calls.futures_change_position_mode(dualSidePosition=False)

        # TODO global margin type option
        # https://binance-docs.github.io/apidocs/futures/en/#exchange-information
        symbols = self.calls.futures_exchange_info()["symbols"]
        base_assets = [s['baseAsset'] for s in symbols]
        quote_assets = [s['quoteAsset'] for s in symbols]

        # filter duplicates, symbols are given as trading pairs
        self.available_currencies = list(set(base_assets + quote_assets))

    def get_products(self) -> list:
        needed = self.needed['products']
        # https://binance-docs.github.io/apidocs/futures/en/#exchange-information
        symbols = self.calls.futures_exchange_info()["symbols"]
        return [
            utils.isolate_specific(
                needed,
                {
                    **symbol,
                    # binance asset ids are weird so just recreate it in the "normal" BASE-QUOTE form
                    'symbol':
                    symbol['baseAsset'] + '-' + symbol['quoteAsset'],
                    'base_asset':
                    symbol['baseAsset'],
                    'quote_asset':
                    symbol['quoteAsset'],
                    'contract_type':
                    symbol['contractType']
                }) for symbol in symbols
        ]

    def get_account(self, filter=None) -> utils.AttributeDict:
        account = self.calls.futures_account()
        needed = self.needed['account']

        # initialize all currency to zero
        accounts = utils.AttributeDict({
            curr: utils.AttributeDict({'available': 0})
            for curr in self.available_currencies
        })

        # write in data from binance
        for asset in account['assets']:
            symbol = utils.to_blankly_symbol(asset['asset'], 'binance')
            accounts[symbol] = utils.AttributeDict(
                utils.isolate_specific(
                    needed, {
                        **asset,
                        'available': asset['availableBalance'],
                    }))

        if filter:
            return accounts[filter]
        return accounts

    def parse_order_response(self, response: dict):
        response = utils.AttributeDict(response)
        return utils.AttributeDict({
            'status': response.status,
            'symbol': response.symbol,
            'id': int(response.orderId),
            'created_at': None,  # TODO
            'funds': None,  # TODO
            'type': response.type,
            'contract_type': 'PERPETUAL',
            'side': response.side,
            'position': response.positionSide,
            'price': response.price,
            'time_in_force': response.timeInForce,
            'stop_price': response.stopPrice,
            'exchange_specific': response
        })

    @utils.order_protection
    def market_order(self,
                     symbol: str,
                     side: str,
                     size: float,
                     position: str = 'BOTH') -> FuturesMarketOrder:
        """
        Places a market order.
        In hedge mode, specify either 'short' or 'long' `position`.
        For one way mode, just `buy` or `sell`.
        """
        symbol = utils.to_exchange_symbol(symbol, "binance")
        params = {
            'type': 'MARKET',
            'symbol': symbol,
            'side': side.upper(),
            'quantity': size,
            'positionSide': position
        }
        response = self.calls.futures_create_order(**params)

        return FuturesMarketOrder(self.parse_order_response(response), params,
                                  self)

    @utils.order_protection
    def limit_order(self,
                    symbol: str,
                    side: str,
                    price: float,
                    size: float,
                    position: str = 'BOTH',
                    time_in_force: str = 'GTC') -> FuturesLimitOrder:
        """
        Places a limit order.
        In hedge mode, specify either 'short' or 'long' `position`.
        For one way mode, just `buy` or `sell`.
        """
        symbol = utils.to_exchange_symbol(symbol, "binance")
        params = {
            'type': 'LIMIT',
            'symbol': symbol,
            'side': side.upper(),
            'price': price,
            'quantity': size,
            'positionSide': position,
            'timeInForce': time_in_force,
        }
        response = self.calls.futures_create_order(**params)

        return FuturesLimitOrder(self.parse_order_response(response), params,
                                 self)

    @utils.order_protection
    def cancel_order(self, symbol: str, order_id: int) -> utils.AttributeDict:
        symbol = utils.to_exchange_symbol(symbol, "binance")
        # this library method is broken for some reason 2021-02-25
        res = self.calls.futures_cancel_order(symbol=symbol, orderId=order_id)
        return self.parse_order_response(res)

    @utils.order_protection
    def set_margin_type(self, symbol: str, margin_type: str):
        """
        Set margin type for this symbol. `margin_type` must be one of 'ISOLATED' or 'CROSSED'.
        """
        symbol = utils.to_exchange_symbol(symbol, "binance")
        self.calls.futures_change_margin_type(symbol=symbol, marginType=margin_type)

    def get_open_orders(self, symbol: str = None) -> list:
        if symbol:
            symbol = utils.to_exchange_symbol(symbol, 'binance')
            orders = self.calls.futures_get_open_orders(symbol=symbol)
        else:
            orders = self.calls.futures_get_open_orders()
        return [self.parse_order_response(order) for order in orders]

    def get_order(self, symbol: str, order_id: int) -> utils.AttributeDict:
        symbol = utils.to_exchange_symbol(symbol, 'binance')
        res = self.calls.futures_get_order(symbol=symbol, orderId=order_id)
        return self.parse_order_response(res)

    def get_price(self, symbol: str) -> float:
        symbol = utils.to_exchange_symbol(symbol, "binance")
        return float(self.calls.futures_mark_price(symbol=symbol)['markPrice'])

    @property
    def account(self) -> utils.AttributeDict:
        return self.get_account()

    @property
    def orders(self) -> list:
        return self.get_open_orders()

    def get_product_history(self, symbol, epoch_start, epoch_stop,
                            resolution) -> pd.DataFrame:
        resolution = blankly.time_builder.time_interval_to_seconds(resolution)

        epoch_start = int(utils.convert_epochs(epoch_start))
        epoch_stop = int(utils.convert_epochs(epoch_stop))

        # TODO dedup this from (non-futures) binance interface
        granularities = {
            60: "1m",
            180: "3m",
            300: "5m",
            900: "15m",
            1800: "30m",
            3600: "1h",
            7200: "2h",
            14400: "4h",
            21600: "6h",
            28800: "8h",
            43200: "12h",
            86400: "1d",
            259200: "3d",
            604800: "1w",
            2592000: "1M"
        }

        if resolution not in granularities:
            utils.info_print(
                "Granularity is not an accepted granularity...rounding to nearest valid value."
            )
            resolution = min(granularities,
                             key=lambda gran: abs(resolution - gran))
        gran_string = granularities[resolution]

        # Figure out how many points are needed
        need = int((epoch_stop - epoch_start) / resolution)
        initial_need = need
        window_open = epoch_start
        history = []

        # Convert coin id to binance coin
        symbol = utils.to_exchange_symbol(symbol, 'binance')
        while need > 1000:
            # Close is always 300 points ahead
            window_close = int(window_open + 1000 * resolution)
            history = history + self.calls.futures_klines(symbol=symbol,
                                                  startTime=window_open * 1000,
                                                  endTime=window_close * 1000,
                                                  interval=gran_string,
                                                  limit=1000)

            window_open = window_close
            need -= 1000
            time.sleep(.2)
            utils.update_progress((initial_need - need) / initial_need)

        # Fill the remainder
        history_block = history + self.calls.futures_klines(
            symbol=symbol,
            startTime=window_open * 1000,
            endTime=epoch_stop * 1000,
            interval=gran_string,
            limit=1000)

        data_frame = pd.DataFrame(history_block,
                                  columns=[
                                      'time', 'open', 'high', 'low', 'close',
                                      'volume', 'close time',
                                      'quote asset volume', 'number of trades',
                                      'taker buy base asset volume',
                                      'taker buy quote asset volume', 'ignore'
                                  ],
                                  dtype=None)
        # Clear the ignore column, why is that there binance?
        del data_frame['ignore']

        # Want them in this order: ['time (epoch)', 'low', 'high', 'open', 'close', 'volume']

        # Time is so big it has to be cast separately for windows
        data_frame['time'] = data_frame['time'].div(1000).astype(int)

        # Cast dataframe
        data_frame = data_frame.astype({
            'open': float,
            'high': float,
            'low': float,
            'close': float,
            'volume': float,
            'close time': int,
            'quote asset volume': float,
            'number of trades': int,
            'taker buy base asset volume': float,
            'taker buy quote asset volume': float
        })

        # Convert time to seconds
        return data_frame.reindex(
            columns=['time', 'low', 'high', 'open', 'close', 'volume'])
