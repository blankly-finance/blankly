import blankly
from blankly import HedgeMode, Side, MarginType


def price_event(price, symbol, state: blankly.FuturesStrategyState):
    state.variables['history'].append(price)
    rsi = blankly.indicators.rsi(state.variables['history'])

    if rsi[-1] < 30:
        # rsi < 30 indicates the asset is undervalued or will rise in price
        # we want to go long.
        if state.interface.positions['BTC-USDT'].size <= 0:
            close_position(symbol, state)
            size = blankly.trunc(state.interface.cash / price, 2)
            state.interface.market_order(symbol, side=Side.BUY, size=size)
    elif rsi[-1] > 70:
        # rsi < 70 indicates the asset is overvalued or will drop in price
        # we want to short the asset.
        if state.interface.positions['BTC-USDT'].size >= 0:
            close_position(symbol, state)
            size = blankly.trunc(state.interface.cash / price, 2)
            state.interface.market_order(symbol, side=Side.SELL, size=size)


def close_position(symbol, state: blankly.FuturesStrategyState):
    size = state.interface.positions[symbol].size
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


def init(symbol, state: blankly.FuturesStrategyState):
    close_position(symbol, state)

    state.interface.set_hedge_mode(HedgeMode.ONEWAY)
    state.interface.set_leverage(symbol, 1)
    state.interface.set_margin_type(symbol, MarginType.ISOLATED)

    state.variables['history'] = state.interface.history(
        symbol, to=150, return_as='deque',
        resolution=state.resolution)['close']


if __name__ == "__main__":
    exchange = blankly.BinanceFutures()
    strategy = blankly.FuturesStrategy(exchange)
    strategy.add_price_event(price_event,
                             init=init,
                             teardown=close_position,
                             symbol='BTC-USDT',
                             resolution='1m')

    strategy.start()
