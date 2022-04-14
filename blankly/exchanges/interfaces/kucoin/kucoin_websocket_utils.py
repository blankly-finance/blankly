import time

from blankly.utils.utils import isolate_specific


def switch_type(stream):
    if stream == "ticker":
        return trade, \
               trade_interface, \
               "time, sequence, price, size, bestAsk, bestAskSize, bestBid, bestBidSize\n"
    elif stream == "level2":
        return no_callback, \
               no_callback, \
               ""
    else:
        return no_callback, no_callback, ""


def no_callback(message):
    return message


def trade(message):
    line = str(time.time()) + "," + message["sequence"] + "," + message["price"] + "," + \
           message["size"] + "," + message["bestAsk"] + "," + message["bestAskSize"] + "," + \
           message["bestBid"] + "," + message["bestBidSize"] + "\n"
    return line


def trade_interface(message):
    # renames = [
    #     ["sequence", "trade_id"]
    # ]
    #
    # message = rename_to(renames, message)

    needed = [
        ["symbol", str],
        ["price", float],
        ["time", float],
        ["trade_id", int],
        ["size", float]
    ]
    message['symbol'] = message['topic'].split(":", 1)[1]
    message['trade_id'] = message['data'].pop('sequence')
    message['price'] = message['data'].pop('price')
    message['size'] = message['data'].pop('size')

    message["time"] = time.time()

    isolated = isolate_specific(needed, message)

    return isolated
