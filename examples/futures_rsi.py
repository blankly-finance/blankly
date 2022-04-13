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
from blankly.futures import FuturesStrategyState, FTXFutures, FuturesStrategy, MarginType


def price_event(price, symbol, state: FuturesStrategyState):
    state.variables['history'].append(price)
    rsi = blankly.indicators.rsi(state.variables['history'])
    position = state.interface.get_position('BTC-USDT')

    if rsi[-1] < 50:
        # rsi < 30 indicates the asset is undervalued or will rise in price
        # we want to go long.
        if position is None or position['size'] <= 0:
            close_position(symbol, state)
            size = blankly.trunc(state.interface.cash / price, 2)
            state.interface.market_order(symbol, side=Side.BUY, size=size)
    elif rsi[-1] > 50:
        # rsi < 70 indicates the asset is overvalued or will drop in price
        # we want to short the asset.
        if position is None or position['size'] >= 0:
            close_position(symbol, state)
            size = blankly.trunc(state.interface.cash / price, 2)
            state.interface.market_order(symbol, side=Side.SELL, size=size)


def close_position(symbol, state: FuturesStrategyState):
    position = state.interface.get_position(symbol)
    if not position:
        return
    size = position['size']
    if size < 0:
        state.interface.market_order(symbol,
                                     Side.BUY,
                                     abs(size),
                                     reduce_only=True)
    elif size > 0:
        state.interface.market_order(symbol,
                                     Side.SELL,
                                     abs(size),
                                     reduce_only=True)


def init(symbol, state: FuturesStrategyState):
    close_position(symbol, state)

    # Set initial leverage and margin type
    state.interface.set_leverage(1, symbol)

    state.interface.set_margin_type(symbol, MarginType.ISOLATED)

    state.variables['history'] = state.interface.history(
        symbol, to=150, return_as='deque',
        resolution=state.resolution)['close']


if __name__ == "__main__":
    exchange = BinanceFutures(keys_path="./tests/config/keys.json",
                              preferences_path="./tests/config/settings.json",
                              portfolio_name="Futures Test Key")

    strategy = FuturesStrategy(exchange)
    strategy.add_price_event(price_event,
                             init=init,
                             teardown=close_position,
                             symbol='BTC-USDT',
                             resolution='1m')

    strategy.backtest(to='1mo', initial_values={'USDT': 10000}, settings_path='./tests/config/usdt_backtest.json')
