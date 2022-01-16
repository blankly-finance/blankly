"""
    Utilities for defining how websockets should integrate
    Copyright (C) 2021 Blankly Finance

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
from typing import List


def switch_type(stream):
    if stream == "ticker":
        return trade, \
               process_trades, \
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


"""
Homogenizes response with uhh coinbase and binance
"""


def process_trades(response: dict) -> List[dict]:
    list_trades: List = []
    num_trades: int = len(response['data'])
    trades_data: List[dict] = response['data']

    needed = [
        ["symbol", str],
        ["price", float],
        ["time", float],
        ["trade_id", int],
        ["size", float]
    ]

    for trade_ in trades_data:
        trade_['symbol'] = response['market']
        trade_['trade_id'] = trade_.pop('id')
        trade_['time'] = utils.epoch_from_iso8601(trade_['time'])
        trade_['symbol'] = trade_['symbol'].replace('/', '-')

        list_trades.append(utils.isolate_specific(needed, trade_))

    assert (num_trades == len(list_trades))

    return list_trades


def trade(received):
    line = str(received["time"]) + "," + str(time.time()) + "," + received["price"] + "," + received[
        "open_24h"] + "," + received["volume_24h"] + "," + received["low_24h"] + "," + received[
               "high_24h"] + "," + received["volume_30d"] + "," + received["best_bid"] + "," + received[
               "best_ask"] + "," + received["last_size"] + "\n"
    return line
