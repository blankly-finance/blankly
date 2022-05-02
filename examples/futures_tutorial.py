import blankly
from blankly import futures, Side
from blankly.futures import FuturesStrategyState


def price_event(price, symbol, state: FuturesStrategyState):
    prev_price = state.variables['prev_price']
    position = state.interface.get_position(symbol)

    # if the price rose more than 1,000 and we don't already have a short position, then short sell
    if not position and price - prev_price >= 1000:
        order_size = (state.interface.cash / price) * 0.99
        state.interface.market_order(symbol, Side.SELL, order_size)

    # if the price stablized and we *do* have a short position, close our position.
    elif position and abs(price - prev_price) <= 100:
        # we use abs(position['size']) here because position['size'] can (and will) be negative, since we have taken a short position.
        state.interface.market_order(symbol, Side.BUY, abs(position['size']), reduce_only=True)

    state.variables['prev_price'] = price


# Helper function to close out a position
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


# This function will be run before our algorithm starts
def init(symbol, state: FuturesStrategyState):
    # Sanity check to make sure we don't have any open positions
    close_position(symbol, state)

    # Give the algo the previous price as context
    last_price = state.interface.history(symbol, to=1, return_as='deque', resolution=state.resolution)['close'][-1]
    state.variables['prev_price'] = last_price


# After our backtest is finished, close all our open positions
def teardown(symbol, state):
    close_position(symbol, state)


if __name__ == "__main__":
    exchange = futures.BinanceFutures()
    strategy = futures.FuturesStrategy(exchange)

    # This line is new!
    strategy.add_price_event(price_event, init=init, teardown=teardown, symbol='BTC-USDT', resolution='1d')

    if blankly.is_deployed:
        strategy.start()
    else:
        strategy.backtest(to='1y',
                          initial_values={'USDT': 10000})  # This is USDT and not USD because we are trading on Binance
