from blankly.enums import MarginType, HedgeMode, Side, PositionMode, TimeInForce, ContractType
from blankly.exchanges.interfaces.ftx.ftx_api import FTXAPI
from blankly.exchanges.interfaces.futures_exchange_interface import FuturesExchangeInterface
from blankly.exchanges.orders.futures.futures_order import FuturesOrder
from blankly.utils import utils as utils, exceptions
import datetime


class FTXFuturesInterface(FuturesExchangeInterface):
    calls: FTXAPI

    @staticmethod
    def get_contract_type(symbol: str) -> ContractType:
        if '-PERP' in symbol:
            return ContractType.PERPETUAL
        elif '-MOVE' in symbol:
            return ContractType.MOVE
        return ContractType.EXPIRING

    def init_exchange(self):
        # will throw exception if our api key is stinky
        self.calls.get_account_info()

    def get_products(self) -> list:
        res = self.calls.list_futures()
        return [
            utils.AttributeDict({
                'symbol': symbol['name'],
                'base': symbol['underlying'],
                'quote': 'USD',
                'contract_type': self.get_contract_type(symbol['name']),
                'exchange_specific': symbol
            }) for symbol in res
        ]

    def get_account(self, filter: str = None) -> utils.AttributeDict:
        balances = self.calls.get_balances()
        coins = self.calls.get_coins()
        accounts = utils.AttributeDict({
            coin['id']: utils.AttributeDict({'available': 0})
            for coin in coins
        })

        for bal in balances:
            accounts[bal['coin']] = utils.AttributeDict({
                'available': float(bal['free']),
                'exchange_specific': bal
            })

        if filter:
            return accounts[filter]
        return accounts

    def get_positions(self, symbol: str = None) -> utils.AttributeDict:
        res = self.calls.get_positions()
        leverage = self.get_leverage()
        return utils.AttributeDict({
            position['future']: utils.AttributeDict({
                'size': position['netSize'],
                'side': PositionMode(position['side'].lower()),
                'entry_price': float(position['entryPrice']),
                'contract_type': self.get_contract_type(position['future']),
                'leverage': leverage,
                'margin_type': MarginType.CROSSED,
                'unrealized_pnl': float(
                    position['unrealizedPnl']),  # TODO not sure on this one
                'exchange_specific': position
            })
            for position in res
        })

    def market_order(self,
                     symbol: str,
                     side: Side,
                     size: float,
                     position: PositionMode = None,
                     reduce_only: bool = None) -> FuturesOrder:
        pass

    def limit_order(self,
                    symbol: str,
                    side: Side,
                    price: float,
                    size: float,
                    position: PositionMode = None,
                    reduce_only: bool = None,
                    time_in_force: TimeInForce = None) -> FuturesOrder:
        raise NotImplementedError

    def take_profit(self,
                    symbol: str,
                    side: Side,
                    price: float,
                    size: float,
                    position: PositionMode = None) -> FuturesOrder:
        raise NotImplementedError

    def stop_loss(self,
                  symbol: str,
                  side: Side,
                  price: float,
                  size: float,
                  position: PositionMode = None) -> FuturesOrder:
        raise NotImplementedError

    @utils.order_protection
    def set_hedge_mode(self, hedge_mode: HedgeMode):
        if hedge_mode == HedgeMode.HEDGE:
            raise Exception('HEDGE mode not supported on FTX Futures')
        pass  # FTX only has ONEWAY mode

    @utils.order_protection
    def set_leverage(self, leverage: int, symbol: str = None):
        if symbol:
            raise Exception(
                'FTX Futures does not allow setting leverage per symbol. Use interface.set_leverage(leverage) to set '
                'account-wide leverage instead. ')
        self.calls.change_account_leverage(leverage)

    def get_leverage(self, symbol: str = None) -> float:
        return self.calls.get_account_info()['leverage']

    @utils.order_protection
    def set_margin_type(self, symbol: str, type: MarginType):
        if type == MarginType.ISOLATED:
            raise Exception('ISOLATED margin not supported on FTX Futures')
        pass

    def cancel_order(self, symbol: str, order_id: int) -> FuturesOrder:
        raise NotImplementedError

    def get_open_orders(self, symbol: str) -> list:
        raise NotImplementedError

    def get_order(self, symbol: str, order_id: int) -> FuturesOrder:
        raise NotImplementedError

    def get_price(self, symbol: str) -> float:
        raise NotImplementedError

    def get_funding_rate_history(self, symbol: str, epoch_start: int,
                                 epoch_stop: int) -> list:
        rates = self.calls.get_funding_rates(epoch_start, epoch_stop, symbol)
        # TODO limit 500
        # TODO timestamp issue
        return [{
            'rate': float(e['rate']),
            'time': datetime.datetime.fromisoformat(e['time']).timestamp()
        } for e in rates]

    def get_product_history(self, symbol, epoch_start, epoch_stop, resolution):
        raise NotImplementedError
