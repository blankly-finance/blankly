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
from alpaca_trade_api.entity_v2 import trade_mapping_v2
from msgpack.ext import Timestamp

from blankly.utils.utils import isolate_specific, rename_to


def parse_alpaca_timestamp(value: Timestamp):
    return value.seconds + (value.nanoseconds * float(1e-9))


def alpaca_remapping(dictionary: dict, mapping: dict):
    # From https://stackoverflow.com/a/67573821/8087739
    try:
        dictionary.pop('T')
    except KeyError:
        pass
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
        return no_logging_callback, no_callback, ""


def no_callback(message):
    return message


def no_logging_callback(message):
    response = ""
    for i in list(message.keys()):
        response += str(message[i])
        response += ','

    response += '\n'
    return response


def trades_logging(message: dict):
    return str(str(message["i"]) + "," +
               str(message["S"]) + "," +
               str(message["c"]) + "," +
               str(message["x"]) + "," +
               str(message["p"]) + "," +
               str(message["s"]) + "," +
               str(message["t"]) + "," +
               str(message["z"]) + "\n")


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
    message['time'] = message.pop('timestamp')

    renames = [
        ["id", "trade_id"],
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
    return str(str(message["S"]) + "," +
               str(message["ax"]) + "," +
               str(message["ap"]) + "," +
               str(message["as"]) + "," +
               str(message["bx"]) + "," +
               str(message["bp"]) + "," +
               str(message["bs"]) + "," +
               str(message["c"]) + "," +
               str(message["t"]) + "," +
               str(message["z"]) + "\n")
