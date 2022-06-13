from blankly.enums import Side
from blankly.exchanges.interfaces.futures_exchange_interface import FuturesExchangeInterface
from blankly.frameworks.strategy import FuturesStrategyState


def close_position(symbol: str, state: FuturesStrategyState):
    """
    Exit a position
    Args:
        state: the StrategyState
        symbol: the symbol to sell
    """
    position = state.interface.get_position(symbol)
    if not position:
        return

    if position['size'] < 0:
        side = Side.BUY
    elif position['size'] > 0:
        side = Side.SELL
    else:
        # wtf?
        return

    state.interface.market_order(symbol, side, abs(position['size']), reduce_only=True)
