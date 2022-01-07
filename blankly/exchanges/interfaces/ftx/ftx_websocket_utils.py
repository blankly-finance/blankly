import time
import copy
import blankly.utils.utils as utils
from typing import List

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

    for trade in trades_data:
        trade['symbol'] = response['market']
        trade['trade_id'] = trade.pop('id')
        trade['time'] = utils.epoch_from_ISO8601(trade['time'])
        trade['symbol'] = trade['symbol'].replace('/', '-')

        list_trades.append(utils.isolate_specific(needed, trade))
    
    assert(num_trades == len(list_trades))

    return list_trades


def trade(received):
    line = str(received["time"]) + "," + str(time.time()) + "," + received["price"] + "," + received[
        "open_24h"] + "," + received["volume_24h"] + "," + received["low_24h"] + "," + received[
               "high_24h"] + "," + received["volume_30d"] + "," + received["best_bid"] + "," + received[
               "best_ask"] + "," + received["last_size"] + "\n"
    return line
