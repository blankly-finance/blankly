import time

from blankly.utils.utils import isolate_specific


def switch_type(stream):
    if stream == "trade":
        return trade, \
               trade_interface, \
               "time, system_time, price, volume, side, order_type, misc\n"
    elif stream == "book":
        return no_callback, \
               no_callback, \
               ""
    else:
        return no_callback, no_callback, ""


def no_callback(message):
    return message


def trade(received):
    line = str(received[1][0][2]) + "," + str(time.time()) + "," + received[1][0][0] + "," + received[1][0][1] + "," + \
           received[1][0][3] + "," + received[1][0][4] + "," + received[1][0][5] + "\n"

    return line



def trade_interface(message):
    symbol = message[3]

    needed = [
        ["symbol", str],
        ["price", float],
        ["time", float],
        ["trade_id", int],
        ["size", float]
    ]

    output_dict = {
    }
    output_dict['symbol'] = symbol.replace("/", "-")
    output_dict['price'] = message[1][0][0]
    output_dict["time"] = message[1][0][2]
    output_dict['trade_id'] = None
    output_dict["size"] = message[1][0][1]

    isolated = isolate_specific(needed, output_dict)

    return isolated
