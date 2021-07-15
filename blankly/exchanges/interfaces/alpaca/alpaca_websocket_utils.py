"""
    Alpaca websocket homogenization definitions.
    Copyright (C) 2021  Emerson Dove

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

import time
from blankly.utils.utils import rename_to, isolate_specific
from alpaca_trade_api.entity_v2 import trade_mapping_v2, quote_mapping_v2, bar_mapping_v2, status_mapping_v2


def parse_alpaca_timestamp(value):
    return value['t'].seconds * int(1e9) + value['t'].nanoseconds


def alpaca_remapping(dictionary: dict, mapping: dict):
    # From https://stackoverflow.com/a/67573821/8087739
    return {mapping[k]: dictionary[k] for k in dictionary}


def switch_type(stream):
    if stream == "trades":
        return trades, \
               trades_interface, \
               "id,symbol,conditions,exchange,price,size,timestamp,tape\n"
    else:
        return no_callback, no_callback, ""


def no_callback(message):
    return message


def trades(message):
    message['t'] = parse_alpaca_timestamp(message['t'])
    return str(message["i"] + "," +
               message["S"] + "," +
               message["c"] + "," +
               message["x"] + "," +
               message["p"] + "," +
               message["s"] + "," +
               message["t"] + "," +
               message["z"] + "\n")


def trades_interface(message):
    """
    Similar ticks with coinbase pro
    {
        'type': 'ticker',
        'symbol': 'BTC-USD',
        'price': '50141.55',
        'time': 1619286924.397969,
        'trade_id': 160775277,
        'size': .35324
    }
    """
    renames = [
        ["e", "type"],
        ["s", "symbol"],
        ["p", "price"],
        ["T", "time"],
        ["t", "trade_id"],
    ]
    message = rename_to(renames, message)

    needed = [
        ["product_id", str],
        ["price", float],
        ["time", int],
        ["trade_id", int],
        ["size", float]
    ]
    message["time"] = message["time"]/1000
    return isolate_specific(needed, message)
