"""
    Futures RSI Example.
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

import blankly
from blankly import Side
from blankly.exchanges.interfaces.binance_futures.binance_futures import BinanceFutures
from blankly.futures import FuturesStrategyState, FuturesStrategy

from blankly.futures.utils import close_position


def price_event(price, symbol, state: FuturesStrategyState):
    state.variables['history'].append(price)

    rsi = blankly.indicators.rsi(state.variables['history'])

    position = state.interface.get_position('BTC-USDT')
    position_size = position['size'] if position else 0

    if rsi[-1] < 30:
        # rsi < 30 indicates the asset is undervalued or will rise in price
        # we want to go long.
        side = Side.BUY
    elif rsi[-1] > 70:
        # rsi < 70 indicates the asset is overvalued or will drop in price
        # we want to short the asset.
        side = Side.SELL
    else:
        close_position(symbol, state)
        return

    if (position_size != 0) and (side == Side.BUY) == (position_size > 0):
        return

    order_size = (state.interface.cash / price) * 0.99

    if order_size <= 0:
        return

    state.interface.market_order(symbol, side=side, size=order_size)


def init(symbol, state: FuturesStrategyState):
    close_position(symbol, state)

    state.variables['history'] = state.interface.history(
        symbol, to=150, return_as='deque',
        resolution=state.resolution)['close']


if __name__ == "__main__":
    exchange = BinanceFutures()

    strategy = FuturesStrategy(exchange)
    strategy.add_price_event(price_event,
                             init=init,
                             teardown=close_position,
                             symbol='BTC-USDT',
                             resolution='5m')

    strategy.backtest(to='1mo', initial_values={'USDT': 10000})
