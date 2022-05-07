import blankly
from blankly import Side
from blankly.exchanges.interfaces.binance_futures.binance_futures import BinanceFutures
from blankly.futures import FuturesStrategyState, FuturesStrategy, MarginType

from blankly.futures.utils import close_position


def price_event(price, symbol, state: FuturesStrategyState):
    state.variables['history'].append(price)
    position = state.interface.get_position('BTC-USDT')
    position_size = position['size'] if position else 0
    precision = state.variables['precision']

    order_size = (state.interface.cash / price) * 0.99
    order_size = blankly.trunc(order_size, precision)

    if not state.variables['order_id']:
        state.variables['order_id'] = state.interface.limit_order(symbol, side=Side.BUY, price=37000,
                                                                  size=order_size).id
    elif not state.variables['canceled']:
        state.interface.cancel_order(symbol, state.variables['order_id'])
        state.variables['canceled'] = True


def init(symbol, state: FuturesStrategyState):
    close_position(symbol, state)

    # Set initial leverage and margin type
    state.interface.set_leverage(1, symbol)

    state.interface.set_margin_type(symbol, MarginType.ISOLATED)

    state.variables['history'] = state.interface.history(
        symbol, to=150, return_as='deque',
        resolution=state.resolution)['close']

    state.variables['precision'] = state.interface.get_products(symbol)['size_precision']
    state.variables['order_id'] = None
    state.variables['canceled'] = False


if __name__ == "__main__":
    exchange = BinanceFutures()

    strategy = FuturesStrategy(exchange)
    strategy.add_price_event(price_event,
                             init=init,
                             teardown=close_position,
                             symbol='BTC-USDT',
                             resolution='1m')

    strategy.backtest(to='1mo', initial_values={'USDT': 10000}, settings_path='./tests/config/usdt_backtest.json')
