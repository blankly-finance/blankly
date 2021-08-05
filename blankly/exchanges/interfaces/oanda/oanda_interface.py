from blankly.exchanges.interfaces.exchange_interface import ExchangeInterface
from blankly.exchanges.interfaces.oanda.oanda_api import OandaAPI
from blankly.exchanges.orders.limit_order import LimitOrder
from blankly.exchanges.orders.market_order import MarketOrder
from blankly.utils import utils as utils


class OandaInterface(ExchangeInterface):
    def __init__(self, authenticated_API: OandaAPI, preferences_path: str):
        super().__init__('oanda', authenticated_API, preferences_path)
        assert isinstance(self.calls, OandaAPI)

    def init_exchange(self):
        assert isinstance(self.calls, OandaAPI)
        account_info = self.calls.get_account()
        assert account_info['account']['id'] is not None, "Oanda exchange account does not exist"

        self.__exchange_properties = {
            "maker_fee_rate": 0,
            "taker_fee_rate": 0
        }

    def get_products(self) -> dict:
        assert isinstance(self.calls, OandaAPI)
        needed = self.needed['get_products']
        instruments = self.calls.get_account_instruments()['instruments']

        for instrument in instruments:
            instrument['symbol'] = instrument.pop('name')
            currencies = instrument['symbol'].split('_')
            instrument['base_asset'] = currencies[0]
            instrument['quote_asset'] = currencies[1]
            instrument['base_min_size'] = float(instrument['minimumTradeSize'])
            instrument['base_max_size'] = float(instrument['maximumOrderUnits'])
            instrument['base_increment'] = 10 ** (-1 * int(instrument['tradeUnitsPrecision']))

        for i in range(len(instruments)):
            instruments[i] = utils.isolate_specific(needed, instruments[i])

        return instruments

    @property
    def cash(self) -> float:
        assert isinstance(self.calls, OandaAPI)
        account_dict = self.calls.get_account()['account']
        return float(account_dict['balance'])

    def get_account(self, symbol=None) -> utils.AttributeDict:
        assert isinstance(self.calls, OandaAPI)
        positions = self.calls.get_all_positions()['positions']
        positions_dict = utils.AttributeDict({})

        for position in positions:
            positions_dict[position['instrument']] = utils.AttributeDict({
                'available': float(position['long']['units']) - float(position['short']['units']),
                'hold': 0
            })

        positions_dict['USD'] = utils.AttributeDict({
            'available': self.cash,
            'hold': 0
        })

        # Now query all open orders and accordingly adjust
        open_orders = self.calls.get_all_open_orders()['orders']
        for position in open_orders:
            # todo: handle other types of orders
            if position['type'] == 'LIMIT':
                if float(position['units']) > 0:
                    positions_dict['USD']['available'] -= float(position['units']) * float(position['price'])
                    positions_dict['USD']['hold'] += float(position['units']) * float(position['price'])
                else:
                    instrument = position['instrument']
                    # sell orders just have a negative 'units'
                    positions_dict[instrument]['available'] -= (-1 * float(position['units']))
                    positions_dict[instrument]['hold'] += (-1 * float(position['units']))

        return positions_dict

    # funds is the base asset (EUR_CAD the base asset is CAD)
    def market_order(self, symbol: str, side: str, funds: float) -> MarketOrder:
        assert isinstance(self.calls, OandaAPI)

        qty_to_buy = funds/self.get_price(symbol)
        if side == "buy":
            pass
        elif side == "sell":
            qty_to_buy *= -1
        else:
            raise ValueError("side needs to be either sell or buy")

        resp = self.calls.place_market_order(symbol, qty_to_buy)

        needed = self.needed['market_order']
        order = {
            'funds': qty_to_buy,
            'side': side,
            'symbol': symbol,
            'type': 'market'
        }

        resp['symbol'] = resp['orderCreateTransaction']['instrument']
        resp['id'] = resp['orderCreateTransaction']['id']
        resp['created_at'] = resp['orderCreateTransaction']['time']
        resp['funds'] = qty_to_buy
        resp['status'] = qty_to_buy
        resp['type'] = 'market'
        resp['side'] = side

        resp = utils.isolate_specific(needed, resp)
        return MarketOrder(order, resp, self)

    # todo: finish implementing
    def limit_order(self, symbol: str, side: str, price: float, quantity: int) -> LimitOrder:
        assert isinstance(self.calls, OandaAPI)
        if side == "buy":
            pass
        elif side == "sell":
            quantity *= -1
        else:
            raise ValueError("side needs to be either sell or buy")

        needed = self.needed['limit_order']
        order = {
            'size': quantity,
            'side': side,
            'price': price,
            'symbol': symbol,
            'type': 'limit'
        }

        resp = self.calls.place_limit_order(symbol, quantity, price)
        return resp

    def cancel_order(self, symbol, order_id) -> dict:
        # Either the Order’s OANDA-assigned OrderID or the Order’s client-provided ClientID prefixed by the “@” symbol
        assert isinstance(self.calls, OandaAPI)
        resp = self.calls.cancel_order(order_id)
        return {'order_id': order_id}

    # todo: homogenize the response
    def get_open_orders(self, symbol=None):
        assert isinstance(self.calls, OandaAPI)
        if symbol is None:
            resp = self.calls.get_all_open_orders()
        else:
            resp = self.calls.get_orders(symbol)

        orders = resp['orders']
        return orders

    def get_order(self, symbol, order_id) -> dict:
        # Either the Order’s OANDA-assigned OrderID or the Order’s client-provided ClientID prefixed by the “@” symbol
        assert isinstance(self.calls, OandaAPI)
        order = self.calls.get_order(order_id)
        return self.homogenize_order(order)

    def get_fees(self):
        assert isinstance(self.calls, OandaAPI)
        return {
            'maker_fee_rate': 0.0,
            'taker_fee_rate': 0.0
        }

    # todo: implement
    def get_product_history(self, symbol: str, epoch_start: float, epoch_stop: float, resolution: int):
        pass

    # todo: implement
    def get_order_filter(self, symbol: str):
        pass

    def get_price(self, symbol: str) -> float:
        resp = self.calls.get_order_book(symbol)['orderBook']['price']
        return float(resp)

    def homogenize_order(self, order):
        if order['order']['type'] == "MARKET":
            order['symbol'] = order['order']['instrument']
            order['id'] = order['order']['id']
            order['created_at'] = order['order']['createTime']

            # TODO: handle status
            order['status'] = order['order']['state']
            order['funds'] = order['order']['units']
            order['type'] = 'market'
            if float(order['order']['units']) < 0:
                order['side'] = 'sell'
            else:
                order['side'] = 'buy'

        # TODO: handle other order types
        needed = self.choose_order_specificity(order['type'])
        order = utils.isolate_specific(needed, order)
        return order
