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
        pass

    @property
    def cash(self):
        account_dict = self.calls.get_account()
        return float(account_dict['balance'])

    def get_account(self, symbol=None):
        pass

    def market_order(self, symbol: str, side: str, funds: float) -> MarketOrder:
        assert isinstance(self.calls, OandaAPI)
        if side == "buy":
            pass
        elif side == "sell":
            funds *= -1
        else:
            raise ValueError("side needs to be either sell or buy")

        needed = self.needed['market_order']
        order = {
            'funds': funds,
            'side': side,
            'symbol': symbol,
            'type': 'market'
        }

        resp = self.calls.place_market_order(symbol, funds)
        resp['symbol'] = resp['orderCreateTransaction']['instrument']
        resp['id'] = resp['orderCreateTransaction']['id']
        resp['created_at'] = resp['orderCreateTransaction']['time']
        resp['funds'] = funds
        resp['status'] = funds
        resp['type'] = 'market'
        resp['side'] = side

        resp = utils.isolate_specific(needed, resp)
        return MarketOrder(order, resp, self)

    def limit_order(self, symbol: str, side: str, price: float, quantity: int) -> LimitOrder:

        pass

    def cancel_order(self, symbol, order_id) -> dict:
        # Either the Order’s OANDA-assigned OrderID or the Order’s client-provided ClientID prefixed by the “@” symbol
        assert isinstance(self.calls, OandaAPI)
        resp = self.calls.cancel_order(order_id)

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

    def get_product_history(self, symbol: str, epoch_start: float, epoch_stop: float, resolution: int):
        pass

    def get_order_filter(self, symbol: str):
        pass

    def get_price(self, symbol) -> float:
        pass

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
