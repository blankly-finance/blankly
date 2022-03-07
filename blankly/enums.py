import enum


class MarginType(str, enum.Enum):
    CROSSED = 'crossed'
    ISOLATED = 'isolated'


class Side(str, enum.Enum):
    BUY = 'buy'
    SELL = 'sell'


class PositionMode(str, enum.Enum):
    BOTH = 'both'
    LONG = 'long'
    SHORT = 'short'


class TimeInForce(str, enum.Enum):
    GTC = 'GTC'  # Good Till Cancelled
    FOK = 'FOK'  # Fill or Kill
    IOC = 'IOC'  # Immediate or Cancel


class HedgeMode(str, enum.Enum):
    HEDGE = 'hedge'
    ONEWAY = 'oneway'


class OrderStatus(str, enum.Enum):
    NEW = 'new'
    PARTIALLY_FILLED = 'partially_filled'
    FILLED = 'filled'
    CANCELED = 'canceled'
    EXPIRED = 'expired'


class OrderType(str, enum.Enum):
    MARKET = 'market'
    LIMIT = 'limit'
    STOP = 'stop'
    TAKE_PROFIT = 'take_profit'
    LIQUIDATION = 'liquidation'


class ContractType(str, enum.Enum):
    PERPETUAL = 'perpetual'
