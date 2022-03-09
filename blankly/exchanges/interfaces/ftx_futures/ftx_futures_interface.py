from blankly import MarginType, HedgeMode, Side, PositionMode, TimeInForce
from blankly.exchanges.interfaces.ftx.ftx_api import FTXAPI
from blankly.exchanges.interfaces.futures_exchange_interface import FuturesExchangeInterface
from blankly.exchanges.orders.futures.futures_order import FuturesOrder
from blankly.utils import utils as utils, exceptions


class FTXFuturesInterface(FuturesExchangeInterface):
    calls: FTXAPI

    def init_exchange(self):
        self.calls.get_account_info()  # will throw exception if our api key is stinky

    def get_products(self) -> list:
        raise NotImplementedError

    def get_account(self, symbol: str = None) -> utils.AttributeDict:
        raise NotImplementedError

    def get_positions(self, symbol: str = None) -> utils.AttributeDict:
        raise NotImplementedError

    def market_order(self, symbol: str, side: Side, size: float, position: PositionMode = None,
                     reduce_only: bool = None) -> FuturesOrder:
        raise NotImplementedError

    def limit_order(self, symbol: str, side: Side, price: float, size: float, position: PositionMode = None,
                    reduce_only: bool = None, time_in_force: TimeInForce = None) -> FuturesOrder:
        raise NotImplementedError

    def take_profit(self, symbol: str, side: Side, price: float, size: float,
                    position: PositionMode = None) -> FuturesOrder:
        raise NotImplementedError

    def stop_loss(self, symbol: str, side: Side, price: float, size: float,
                  position: PositionMode = None) -> FuturesOrder:
        raise NotImplementedError

    def set_hedge_mode(self, hedge_mode: HedgeMode):
        raise NotImplementedError

    def set_leverage(self, symbol: str, leverage: int) -> float:
        raise NotImplementedError

    def set_margin_type(self, symbol: str, type: MarginType):
        raise NotImplementedError

    def cancel_order(self, symbol: str, order_id: int) -> FuturesOrder:
        raise NotImplementedError

    def get_open_orders(self, symbol: str) -> list:
        raise NotImplementedError

    def get_order(self, symbol: str, order_id: int) -> FuturesOrder:
        raise NotImplementedError

    def get_price(self, symbol: str) -> float:
        raise NotImplementedError

    def get_funding_rate_history(self, symbol: str, epoch_start: int, epoch_stop: int) -> list:
        raise NotImplementedError

    def get_product_history(self, symbol, epoch_start, epoch_stop, resolution):
        raise NotImplementedError

