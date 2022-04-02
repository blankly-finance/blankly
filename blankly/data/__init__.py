import enum as __enum
from .data_reader import DataReader


class DataTypes(__enum):
    ohlcv_csv = 0
    ohlcv_json = 1
    event_json = 2

"""
Some datatype examples


ohlcv_csv
symbol1, time, open, high, low, close, volume, symbol2, time, open, high, low, close, volume


ohlcv_json
{
    "symbol": {
        "open": [],
        "high": [],
        "low": [],
        "close": [],
        "volume": []
    }
}


event_json
{
    "event_type": {
        time: {
            "any": "event details"
        }
    }

}
"""
