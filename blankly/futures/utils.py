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
    position = state.interface.interface.get_position(symbol)
    if not position:
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

    # TODO: CRITICAL! UNCOMMENT THE RIGHT LINE FOR YOUR USE CASE! SHOULD FIND A SOLID SOLUTION FOR BOTH CASES!!!
    state.interface.market_order(symbol, side, abs(position['size']), reduce_only=True)  # Use this line when backtesting
    # state.interface.interface.market_order(symbol, side, abs(position['size']), reduce_only=True)  # Use this line when live


def close_partialy_position(symbol: str, state: FuturesStrategyState, size):
    """
    Exit a part of the position
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

    if abs(position['size']) < size:
        return

    state.interface.market_order(symbol, side, size, reduce_only=True)
