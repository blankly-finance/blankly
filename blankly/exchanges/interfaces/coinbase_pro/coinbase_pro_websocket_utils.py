"""
    Websocket feeds need to be modular due to the subscription methods, this provides dynamic management for CBP.
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
    if stream == "ticker":
        return trade, \
               trade_interface, \
               "time,system_time,price,open_24h,volume_24h,low_24h,high_24h,volume_30d,best_bid,best_ask," \
               "last_size\n"
    elif stream == "level2":
        return no_callback, \
               no_callback, \
               ""
    else:
        return no_callback, no_callback, ""


def no_callback(message):
    return message


def trade(received):
    line = str(received["time"]) + "," + str(time.time()) + "," + received["price"] + "," + received[
        "open_24h"] + "," + received["volume_24h"] + "," + received["low_24h"] + "," + received[
               "high_24h"] + "," + received["volume_30d"] + "," + received["best_bid"] + "," + received[
               "best_ask"] + "," + received["last_size"] + "\n"
    return line


def trade_interface(message):
    """
    Homogenizing with binance's return:

    Args:
        message (dict): Message from the exchange.
    """
    needed = [
        ["symbol", str],
        ["price", float],
        ["time", float],
        ["trade_id", int],
        ["size", float]
    ]

    message['symbol'] = message.pop('product_id')
    message['size'] = message.pop('last_size')
    return utils.isolate_specific(needed, message)
