from collections import defaultdict
from typing import List, Optional

from blankly import Side, TimeInForce
from blankly.enums import MarginType, HedgeMode, PositionMode
from blankly.exchanges.interfaces.futures_exchange_interface import FuturesExchangeInterface
from blankly.exchanges.orders.futures.futures_order import FuturesOrder
from blankly.utils import utils as utils


class FuturesPaperTradeInterface(FuturesExchangeInterface):
    interface: FuturesExchangeInterface
    account: dict
    positions: dict

    def __init__(self, exchange_name: str, interface: FuturesExchangeInterface, account_values: dict = None):
        super().__init__(exchange_name, interface.calls)
        self.interface = interface

        # same functionality as 'real' FuturesExchangeInterface's
        self.account = defaultdict(lambda: {'available': 0, 'hold': 0})

        # if python3.9 we could use the new dict update operator here :(
        self.account.update({
            asset: {'available': value, 'hold': 0} for asset, value in account_values
        })

        self.positions = {}

    def init_exchange(self):
        self.interface.init_exchange()

    def get_products(self, symbol: str = None) -> dict:
        return self.interface.get_products(symbol)

    def get_account(self, symbol: str = None) -> utils.AttributeDict:
        return utils.AttributeDict(self.account)

    def get_positions(self, symbol: str = None) -> Optional[dict]:
        return self.positions

    def market_order(self, symbol: str, side: Side, size: float, position: PositionMode = None,
                     reduce_only: bool = None) -> FuturesOrder:
        pass

    def limit_order(self, symbol: str, side: Side, price: float, size: float, position: PositionMode = None,
                    reduce_only: bool = None, time_in_force: TimeInForce = None) -> FuturesOrder:
        pass

    def take_profit(self, symbol: str, side: Side, price: float, size: float,
                    position: PositionMode = None) -> FuturesOrder:
        pass

    def stop_loss(self, symbol: str, side: Side, price: float, size: float,
                  position: PositionMode = None) -> FuturesOrder:
        pass

    def set_hedge_mode(self, hedge_mode: HedgeMode):
        pass

    def get_hedge_mode(self):
        pass

    def set_leverage(self, leverage: int, symbol: str = None):
        pass

    def get_leverage(self, symbol: str = None) -> float:
        pass

    def set_margin_type(self, symbol: str, type: MarginType):
        pass

    def get_margin_type(self, symbol: str):
        pass

    def cancel_order(self, symbol: str, order_id: int) -> FuturesOrder:
        pass

    def get_open_orders(self, symbol: str = None) -> List[FuturesOrder]:
        pass

    def get_order(self, symbol: str, order_id: int) -> FuturesOrder:
        pass

    def get_price(self, symbol: str) -> float:
        pass

    def get_funding_rate_history(self, symbol: str, epoch_start: int, epoch_stop: int) -> list:
        pass

    def get_funding_rate_resolution(self) -> int:
        pass

    def get_product_history(self, symbol, epoch_start, epoch_stop, resolution):
        pass
