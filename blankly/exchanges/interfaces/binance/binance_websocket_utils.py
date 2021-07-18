"""
    Websocket feeds need to be modular due to the subscription methods, this provides dynamic management for binance.
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

import blankly.utils.utils as utils


def switch_type(stream):
    if stream == "trade":
        return trade, \
               trade_interface, \
               "event_time,system_time,event_type,symbol,trade_id,price,quantity,buyer_order_id,seller_order_id," \
               "trade_time,buyer_is_maker\n"
    elif stream == "depth":
        return depth, depth_interface, ""
    else:
        return no_callback, no_callback, ""


def no_callback(message):
    return message


def depth(message):
    return message


def depth_interface(message):
    return message


def trade(message):
    return str(message["E"]) + "," + str(time.time()) + "," + message["e"] + "," + message["s"] + "," + \
           str(message["t"]) + "," + message["p"] + "," + message["q"] + "," + str(message["b"]) + "," + \
           str(message["a"]) + "," + str(message["T"]) + "," + str(message["m"]) + "\n"


def trade_interface(message):
    """
    Homogenizing with coinbase's return:
    {'type': 'ticker', 'sequence': 24587251151, 'symbol': 'BTC-USD', 'price': '56178.52', 'open_24h': '56881.78',
    'volume_24h': '17606.23228984', 'low_24h': '55288', 'high_24h': '58400', 'volume_30d': '506611.70878868',
    'best_bid': '56171.12', 'best_ask': '56178.53', 'side': 'sell', 'time': 1620331254.43236, 'trade_id': 165659167,
    'last_size': '0.04'}

    Response from trade streams
    {
        'e': 'trade',  # Event Type
        'E': 1619149864634,  # Event time
        's': 'BTCUSDT', # Symbol
        't': 787178035,  # Trade ID
        'p': '50322.05000000',  # Price
        'q': '0.00577200',  # Quantity
        'b': 5644954701,  # Buyer order id
        'a': 5644954632,  # Seller order id
        'T': 1619149864634,  # Trade time
        'm': False,  # Is the buyer the market maker?
        'M': True  # Ignore
    }

    Similar ticks with coinbase pro
    {
        'type': 'ticker',
        'symbol': 'BTC-USD',
        'price': '50141.55',
        'time': 1619286924.397969,
        'trade_id': 160775277,
        'size': .3432
    }
    """
    renames = [
        ["e", "type"],
        ["s", "symbol"],
        ["p", "price"],
        ["T", "time"],
        ["t", "symbol"],
        ['q', "size"]
    ]
    message = utils.rename_to(renames, message)
    needed = [
        ["symbol", str],
        ["price", float],
        ["time", float],
        ["trade_id", int],
        ["size", float]
    ]
    message["time"] = message["time"] / 1000
    return utils.isolate_specific(needed, message)
