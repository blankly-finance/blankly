from blankly.exchanges.interfaces.exchange_interface import ExchangeInterface
from blankly.exchanges.interfaces.oanda.oanda_api import OandaAPI
from blankly.exchanges.orders.limit_order import LimitOrder
from blankly.exchanges.orders.market_order import MarketOrder


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

    def market_order(self, symbol, side, funds) -> MarketOrder:
        pass

    def limit_order(self, symbol: str, side: str, price: float, quantity: int) -> LimitOrder:
        pass

    def cancel_order(self, symbol, order_id) -> dict:
        # Either the Order’s OANDA-assigned OrderID or the Order’s client-provided ClientID prefixed by the “@” symbol
        assert isinstance(self.calls, OandaAPI)
        resp = self.calls.cancel_order(order_id)
        pass

    def get_open_orders(self, symbol=None):
        assert isinstance(self.calls, OandaAPI)
        if symbol is None:
            resp = self.calls.get_all_open_orders()
        else:
            resp = self.calls.get_orders(symbol)

        orders = resp['orders']
        pass

    def get_order(self, symbol, order_id) -> dict:
        # Either the Order’s OANDA-assigned OrderID or the Order’s client-provided ClientID prefixed by the “@” symbol
        assert isinstance(self.calls, OandaAPI)
        resp = self.calls.get_order(order_id)
        pass

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