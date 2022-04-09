import time
import blankly.utils.utils as utils


def switch_type(stream):
    if stream == "tickers":
        return trade, \
               trade_interface, \
               "time, system_time, price, open_24h, volume_24h, low_24h, high_24h, best_bid, best_ask," \
               "last_traded_price, last_traded_size\n"

    elif stream == "books":
        return no_callback, \
               no_callback, \
               ""
    else:
        return no_callback, no_callback, ""


def no_callback(message):
    return message


def trade(received):
    line = str(received['data']['ts'] / 1000) + "," + str(time.time()) + "," + received['data']['sodUtc0'] + "," + \
           received[
               'data']['open24h'] + "," + received['data']['volCcy24h'] + "," + received['data']['low24h'] + "," + \
           received[
               'data']['high24h'] + "," + received['data']['bidSz'] + "," + received['data']['askSz'] + "," + received[
               'data']['last'] + "," + received['data']['lastSz'] + "\n"
    return line


def trade_interface(message):
    needed = [
        ["symbol", str],
        ["price", float],
        ["time", float],
        ["trade_id", int],
        ["size", float]
    ]

    symbol = message['instId']
    new_symbol = '-'.join(symbol.split('-')[:2])
    message['symbol'] = new_symbol
    message['size'] = message['lastSz']
    message['trade_id'] = None
    message['price'] = message['last']
    message['time'] = message['ts']

    return utils.isolate_specific(needed, message)
