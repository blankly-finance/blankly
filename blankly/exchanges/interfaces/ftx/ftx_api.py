"""
    General FTX Api definition
    Copyright (C) 2021 Blankly Finance

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


import requests
from typing import Optional, Dict, Any, List
import urllib.parse
from blankly.utils.utils import epoch_from_iso8601
import time
import hmac


class FTXAPI:
    _API_URL = "https://ftx.us/api/"

    # no option to instantiate with sandbox mode, unlike every other exchange
    def __init__(self, api_key, api_secret, _subaccount_name=None):

        self._ftx_session = requests.Session()
        self._api_key = api_key
        self._api_secret = api_secret
        self._subaccount_name = _subaccount_name

    def _signed_request(self, method: str, path: str, **kwargs):
        request = requests.Request(method, self._API_URL + path, **kwargs)
        self._get_signature(request)
        result = self._ftx_session.send(request.prepare())
        return self._handle_response(result)

    def _get_signature(self, request: requests.Request):
        ts = int(1000 * time.time())
        prepared_request = request.prepare()
        signed_data = f'{ts}{prepared_request.method}{prepared_request.path_url}'.encode()

        if prepared_request.body:
            signed_data += prepared_request.body

        signature = hmac.new(self._api_secret.encode(), signed_data, 'sha256').hexdigest()

        request.headers['FTXUS-KEY'] = self._api_key
        request.headers['FTXUS-SIGN'] = signature
        request.headers['FTXUS-TS'] = str(ts)

        if self._subaccount_name:
            request.headers['FTXUS-SUBACCOUNT'] = urllib.parse.quote(self._subaccount_name)

    def _signed_delete(self, path: str, params: Optional[Dict[str, Any]] = None):
        return self._signed_request('DELETE', path, json=params)

    def _signed_get(self, path: str, params: Optional[Dict[str, Any]] = None):
        return self._signed_request('GET', path, params=params)

    def _signed_post(self, path: str, params: Optional[Dict[str, Any]] = None):
        return self._signed_request('POST', path, json=params)

    @staticmethod
    def _handle_response(response: requests.Response):
        try:
            result = response.json()

        except ValueError:
            response.raise_for_status()
            raise

        else:
            if not result['success']:
                raise Exception(result['error'])
            else:
                return result['result']

    def list_markets(self) -> List[dict]:

        return self._signed_get('markets')

    def get_market(self, symbol: str) -> dict:

        # symbol format must be BTC/USD instead of BTC-USD
        if '-' in symbol:
            symbol = symbol.replace("-", "/")

        return self._signed_get(f'markets/{symbol}')

    def list_futures(self) -> List[dict]:
        return self._signed_get('futures')

    def get_product_history(self, symbol: str, epoch_start: float, epoch_stop: float, resolution) -> List[dict]:
        return self._signed_get(
            f"/markets/{symbol}/candles?resolution={resolution}&start_time={epoch_start}&end_time={epoch_stop}")

    def get_orderbook(self, market: str, depth: int = None) -> dict:
        return self._signed_get(f'markets/{market}/orderbook', {'depth': depth})

    def get_trades(self, market: str) -> dict:
        return self._signed_get(f'markets/{market}/trades')

    def get_account_info(self) -> dict:
        return self._signed_get('account')

    def get_open_orders(self, market: str = None) -> List[dict]:
        return self._signed_get('orders', {'market': market})

    def get_order_by_id(self, order_id: str) -> dict:
        return self._signed_get(f'orders/{order_id}')

    def get_fills(self) -> List[dict]:
        return self._signed_get('fills')

    def get_balances(self) -> List[dict]:
        return self._signed_get('wallet/balances')

    def get_deposit_addresses(self, ticker: str) -> dict:
        return self._signed_get(f'wallet/deposit_addresses/{ticker}')

    def get_positions(self, display_price_avg: bool = False) -> List[dict]:
        return self._signed_get('positions', {'showAvgPrice': display_price_avg})

    def get_specific_position(self, pos_name: str, display_price_avg: bool = False) -> dict:
        filtered = filter(lambda pos: pos['future'] == pos_name, self.get_positions(display_price_avg))
        return next(filtered, None)

    def get_order_history(
            self,
            market: str = None,
            side: str = None,
            order_type: str = None,
            interval_start: float = None,
            interval_end: float = None
    ) -> List[dict]:
        return self._signed_get('orders/history', {
            'market': market,
            'side': side,
            'orderType': order_type,
            'start_time': interval_start,
            'end_time': interval_end})

    def get_conditional_order_history(
            self,
            market: str = None,
            side: str = None,
            type_: str = None,
            order_type: str = None,
            interval_start: float = None,
            interval_end: float = None
    ) -> List[dict]:
        return self._signed_get(f'conditional_orders/history', {
            'market': market,
            'side': side,
            'type': type_,
            'orderType': order_type,
            'start_time': interval_start,
            'end_time': interval_end
        })

    def get_conditional_orders(self, market: str = None) -> List[dict]:
        return self._signed_get(f'conditional_orders', {'market': market})

    def place_order(
            self,
            market: str,
            side: str,
            price: float,
            size: float,
            order_type: str = 'limit',
            reduce_only: bool = False,
            ioc: bool = False,
            post_only: bool = False,
            client_id: str = None
    ) -> dict:
        return self._signed_post('orders', {
            'market': market,
            'side': side,
            'price': price,
            'size': size,
            'type': order_type,
            'reduceOnly': reduce_only,
            'ioc': ioc,
            'postOnly': post_only,
            'clientId': client_id
        })

    def cancel_order(self, order_id: str) -> dict:
        return self._signed_delete(f'orders/{order_id}')

    """
        MUST SPECIFY EXACTLY 1 OF THE FOLLOWING
        order_id XOR existing_client_order_id
    """

    def modify_order(
            self,
            order_id: Optional[str] = None,
            existing_client_order_id: Optional[str] = None,
            client_order_id: Optional[float] = None,
            price: Optional[float] = None,
            size: Optional[float] = None,
    ) -> dict:

        assert (price is None) or (size is None), \
            'You must modify the price or the size'

        assert (existing_client_order_id is None) ^ (order_id is None), \
            'Specify exactly one ID to modify'

        if order_id:
            endpoint_path = f"orders/{order_id}/modify"
        elif existing_client_order_id:
            endpoint_path = f"orders/by_client_id/{existing_client_order_id}/modify"
        else:
            raise AttributeError('Either client_order_id or existing_client_order_id is required')

        if size is None:
            size_json = {}
        else:
            size_json = {'size': size}

        if price is None:
            price_json = {}
        else:
            price_json = {'price': price}

        if client_order_id is None:
            client_order_id_json = {}
        else:
            client_order_id_json = {'clientId': client_order_id}

        return self._signed_post(endpoint_path, {
            **size_json,
            **price_json,
            **client_order_id_json
        })

    """
    to send...
    stop market order: set type = "stop" and specify a trigger price
    stop limit order: also supply a limit price
    take profit market order: set type = "trailing_stop" and specify a trigger price
    """

    def place_conditional_order(
            self,
            market: str,
            side: str,
            size: float,
            order_type: str = "stop",
            limit_price: float = "None",
            reduce_only: bool = False,
            cancel_limit_on_trigger: bool = True,
            trigger_price: float = None,
            trail_value: float = None
    ) -> dict:
        assert type in ['stop', 'take_profit', 'trailing_stop']
        assert type not in ['stop',
                            'take_profit'] or trigger_price is not None, "stop losses and take profits requires a " \
                                                                         "trigger price"
        assert type not in ['trailing stop'] or (
                    trail_value is not None and trigger_price is not None), "must specify trail value for trailing " \
                                                                            "stop, cannot use trigger price"
        return self._signed_post(
            'conditional_orders',
            {
                'market': market,
                'side': side,
                'triggerPrice': trigger_price,
                'size': size,
                'reduceOnly': reduce_only,
                'type': order_type,
                'cancelLimitOnTrigger': cancel_limit_on_trigger,
                'orderPrice': limit_price
            }
        )

    def get_all_trades(self, market: str, interval_start: float = None, interval_end: float = None, lim=100) -> List:

        to_return = []
        set_of_ids = set()

        while True:
            resp = self._signed_get(f'markets/{market}/trades', {
                'end_time': interval_end,
                'start_time': interval_start
            })

            dd_trades = []

            for elem in resp:
                if elem['id'] not in set_of_ids:
                    dd_trades.append(elem)

            to_return.extend(dd_trades)

            set_of_ids |= {elem['id'] for elem in dd_trades}

            if len(resp) == 0:
                break
            interval_end = min(epoch_from_iso8601(time_['time']) for time_ in resp)
            if lim > len(resp):
                break

        return to_return
