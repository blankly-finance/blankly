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


from blankly.utils.utils import rename_to, isolate_specific
from alpaca_trade_api.entity_v2 import trade_mapping_v2, quote_mapping_v2, bar_mapping_v2, status_mapping_v2


def parse_alpaca_timestamp(value):
    return value['t'].seconds * int(1e9) + value['t'].nanoseconds


def alpaca_remapping(dictionary: dict, mapping: dict):
    # From https://stackoverflow.com/a/67573821/8087739
    return {mapping[k]: dictionary[k] for k in dictionary}


def switch_type(stream):
    if stream == "trades":
        return trades_logging, \
               trades_interface, \
               "id,symbol,conditions,exchange,price,size,timestamp,tape\n"
    elif stream == "quotes":
        return quotes_logging, \
               no_callback, \
               "symbol,ask_exchange,ask_price,ask_size,bid_exchange,bid_price,bid_size,conditions,timestamp,tape\n"
    else:
        return no_callback, no_callback, ""


def no_callback(message):
    return message


def trades_logging(message):
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
    message = alpaca_remapping(message, trade_mapping_v2)
    message['time'] = parse_alpaca_timestamp(message.pop('timestamp'))

    renames = [
        ["id", "trade_id"],
        ["timestamp", "time"]
    ]

    message = rename_to(renames, message)

    needed = [
        ["symbol", str],
        ["price", float],
        ["time", float],
        ["trade_id", int],
        ["size", float]
    ]
    return isolate_specific(needed, message)


def quotes_logging(message):
    message['t'] = parse_alpaca_timestamp(message['t'])
    return str(message["S"] + "," +
               message["ax"] + "," +
               message["ap"] + "," +
               message["as"] + "," +
               message["bx"] + "," +
               message["bp"] + "," +
               message["bs"] + "," +
               message["c"] + "," +
               message["t"] + "," +
               message["z"] + "\n")
