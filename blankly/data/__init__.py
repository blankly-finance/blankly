"""
    Datareader types & imports
    Copyright (C) 2022  Emerson Dove

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


from enum import Enum as __Enum


class DataTypes(__Enum):
    ohlcv_csv = 0
    tick_csv = 1
    ohlcv_json = 2
    event_json = 3


from .data_reader import PriceReader, JsonEventReader, TickReader


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
        "time": [],
        "data": []
    }

}
"""
