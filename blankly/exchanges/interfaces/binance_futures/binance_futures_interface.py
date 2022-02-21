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

import binance.error
from binance.futures import Futures as FuturesClient

import blankly.utils.exceptions as exceptions
import blankly.utils.utils as utils
from blankly.exchanges.interfaces.futures_exchange_interface import FuturesExchangeInterface
from blankly.exchanges.orders.futures.futures_limit_order import FuturesLimitOrder
from blankly.exchanges.orders.futures.futures_market_order import FuturesMarketOrder


class BinanceFuturesInterface(FuturesExchangeInterface):
    calls: FuturesClient

    def __init__(self, exchange_name, authenticated_api):
        super().__init__(exchange_name, authenticated_api)

    def init_exchange(self):
        try:
            self.calls.account()
            # TODO set/query margin type, leverage, and position type
        except binance.error.ClientError as e:
            raise exceptions.APIException(
                f"{e.error_message}. Are you trying to use your normal exchange keys while in sandbox mode? \nTry "
                "toggling the 'use_sandbox' setting in your settings.json or check if the keys were input "
                "correctly into your keys.json.")

        # uncomment if you're feeling sexy
        # self.available_currencies = list({
        #     asset
        #     for symbol in self.calls.exchange_info()["symbols"]
        #     for asset in [symbol['baseAsset'], symbol['quoteAsset']]
        # })

        # https://binance-docs.github.io/apidocs/futures/en/#exchange-information
        symbols = self.calls.exchange_info()["symbols"]
        base_assets = [s['baseAsset'] for s in symbols]
        quote_assets = [s['quoteAsset'] for s in symbols]

        # filter duplicates, symbols are given as trading pairs
        self.available_currencies = list(set(base_assets + quote_assets))

    def get_products(self) -> list:
        needed = self.needed['get_products']
        # https://binance-docs.github.io/apidocs/futures/en/#exchange-information
        symbols = self.calls.exchange_info()["symbols"]
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

    def get_account(self, symbol=None) -> utils.AttributeDict:
        account = self.calls.account()
        needed = self.needed['get_account']

        # initialize all currency to zero
        accounts = utils.AttributeDict(
            {curr: {
                'available': 0
            }
             for curr in self.__available_currencies})

        # write in data from binance
        for asset in account['assets']:
            accounts[asset['asset']] = utils.isolate_specific(
                needed, {
                    **asset,
                    'available': asset['availableBalance'],
                })

        if symbol:
            return accounts[symbol]
        return accounts

    def _parse_order_response(self, response: dict):
        # 'order': [["status", str], ["symbol", str], ["id", str],
        #           ["created_at", float], ["funds", float],
        #           ["type", str], ["contract_type", str], ["side", str],
        #           ["position", str], ["price", float], ["time_in_force", str],
        #           ["stop_price", float]],
        response = utils.AttributeDict(response)
        return utils.AttributeDict({
            'status': response.status,
            'symbol': response.symbol,
            'id': response.orderId,
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
        params = {
            'type': 'MARKET',
            'symbol': symbol,
            'side': side.upper(),
            'quantity': size,
            'positionSide': position
        }
        response = self.calls.new_order(**params)

        return FuturesMarketOrder(self._parse_order_response(response), params, self)

    @utils.order_protection
    def limit_order(self, symbol: str, side: str, price: float, size: float,
                    position: str = 'BOTH', time_in_force: str = 'GTC') -> FuturesLimitOrder:
        """
        Places a limit order.
        In hedge mode, specify either 'short' or 'long' `position`.
        For one way mode, just `buy` or `sell`.
        """
        params = {
            'type': 'LIMIT',
            'symbol': symbol,
            'side': side.upper(),
            'price': price,
            'quantity': size,
            'positionSide': position,
            'timeInForce': time_in_force,
        }
        response = self.calls.new_order(**params)

        return FuturesLimitOrder(self._parse_order_response(response), params, self)

    @utils.order_protection
    def cancel_order(self, symbol: str, order_id: int) -> dict:
        self.calls.cancel_order(self, symbol, order_id)

    @utils.order_protection
    def close_position(self, symbol: str = None):
        pass

    def get_open_orders(self, symbol: str = None) -> list:
        raise NotImplementedError

    def get_order(self, order_id: str) -> dict:
        raise NotImplementedError

    def get_price(self, symbol: str) -> float:
        raise NotImplementedError

    @property
    def account(self) -> utils.AttributeDict:
        return self.get_account()

    @property
    def orders(self) -> list:
        pass

    @property
    def cash(self) -> float:
        pass

    def get_product_history(self, symbol, epoch_start, epoch_stop, resolution):
        pass
