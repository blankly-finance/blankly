"""

ATTENTION:
FTX has NO sandbox mode, these are methods specifically designed
to test interface methods which interact with LIVE orders, and 
move REAL funds. It is not recommended that you run these tests.
They must be executed individually and with great caution. Blankly
is not responsible for losses incurred by improper use of this test. 

How do we test methods which affect live funds?

There are 5 main methods that need to be tested which involve
using live funds

1. get_open_orders()
2. market_order()
3. limit_order()
4. cancel_order

We test these by creating a series of assertations that can only
pass if everything works properly. 

"""

import time
import sys

import blankly
from pathlib import Path
from typing import List

from blankly.exchanges.interfaces.ftx.ftx_interface import FTXInterface
import test_ftx_interface_utils as test_utils


def ftx_interface() -> FTXInterface:
    keys_file_path = Path("../../../config/keys.json").resolve()
    settings_file_path = Path("../../../config/settings.json").resolve()

    ftx = blankly.FTX(keys_path=keys_file_path,
                               settings_path=settings_file_path,
                               portfolio_name='Main Account')

    # auth_obj = FTXAuth(str(keys_file_path), "Main Account")
    # _, ftx_interface = DirectCallsFactory.create("ftx", auth_obj, str(settings_file_path))
    return ftx.interface


"""
cancels ALL open orders and distributes funds for testing purposes

pass command line argument reset to activate

use with extreme caution

"""


def reset(ftx_interface: FTXInterface):
    validation = input(
        "Continuing with this test will cancel ALL existing open orders and redistribute funds for testing purposes. "
        "Continue (Y/n)? ")
    if validation.lower() != "y":
        print("aborting test")
        quit()

    for order in ftx_interface.get_open_orders():
        ftx_interface.cancel_order("BTC/USD", order["id"])


def main():
    interface: FTXInterface = ftx_interface()

    validation = input(
        "To complete this test properly, you should have around $10 in USD in your FTX account.\nThis test will "
        "involve the conversion of no more than $10 to BTC.\nDo not have any trades going on while completing this "
        "test.\nContinue (Y/n)? ")
    if validation.lower() != "y":
        quit()

    if len(sys.argv) == 2:
        if sys.argv[1] == "reset":
            reset(interface)
        else:
            print("Invalid command line argument. Aborting")

    # start testing ###

    initial_num_open_orders = len(interface.get_open_orders())

    # creates a buy limit order unlikely to be fulfilled (buying a bitcoin for $5)
    limit_order = interface.limit_order("BTC/USD", "buy", 1, 5)
    assert len(
        interface.get_open_orders()) == 1 + initial_num_open_orders, f"expected {1 + initial_num_open_orders} " \
                                                                     f"but got {len(interface.get_open_orders())}"
    assert limit_order.get_status()['status'] == "new" or limit_order.get_status()[
        'status'] == "open", f"expected open but got {limit_order.get_status()['status']} of " \
                             f"type {type(limit_order.get_status()['status'])}"

    open_order_ids: List[int] = test_utils.get_open_order_ids(interface.get_open_orders())
    limit_order_id = limit_order.get_id()
    assert limit_order_id in open_order_ids, f"id {limit_order_id} (type: {type(limit_order_id)}) not in " \
                                             f"list {open_order_ids} (type: {type(open_order_ids)})"

    # cancels the open limit order
    order_id = int(interface.cancel_order("BTC/USD", limit_order.get_id()))

    # wait for order cancellation to go through
    print("waiting for order cancellation to be accepted")
    while interface.get_order("BTC/USD", order_id)["status"] != "closed":
        print(
            f"waiting for order to be cancelled. Current status: " + interface.get_order("BTC/USD", order_id)["status"],
            end='\r')
        time.sleep(1)
    time.sleep(5)
    assert (interface.get_order("BTC/USD", order_id)["status"] == "closed")
    print("order successfully cancelled")

    curr_num_open_orders = len(interface.get_open_orders())
    assert curr_num_open_orders == initial_num_open_orders, f"expected {initial_num_open_orders} " \
                                                            f"open orders, but got {curr_num_open_orders}\nopen " \
                                                            f"order list:\n{interface.get_open_orders()}"
    assert order_id not in test_utils.get_open_order_ids(interface.get_open_orders())

    # creates a buy market order for $5 worth of bitcoin
    market_order = interface.market_order("BTC/USD", "buy", 5 / interface.get_price("BTC/USD"))

    curr_order_status = ""
    # waits for status of market order to update
    while curr_order_status != "closed":
        curr_order_status = interface.get_order("BTC/USD", market_order.get_id())["status"]
        print("waiting for test market order to get accepted. Current status: " + curr_order_status, end='\r')
        time.sleep(1)

    time.sleep(5)

    print("Test market order accepted... waiting for status to update")

    market_order_info = interface.get_order("BTC/USD", market_order.get_id())

    assert market_order.get_id() not in test_utils.get_open_order_ids(interface.get_open_orders())
    assert market_order_info["id"] == market_order.get_id()
    market_order_status = market_order_info["status"]
    assert market_order_status == "closed", f"expected closed, but got {market_order_status} (type: " \
                                            f"{type(market_order_status)}) \nopen orders: {interface.get_open_orders()}"

    # creates a sell limit order unlikely to get fulfilled (selling ~$5 worth of bitcoin for $50,000)
    price = 50000
    size = 5 / interface.get_price("BTC/USD")
    print(f"Attempting to create a limit order of {size} BTC for {price} USD")
    limit_order = interface.limit_order("BTC/USD", "sell", price, size)

    curr_open_orders = test_utils.get_open_order_ids(interface.get_open_orders())
    assert limit_order.get_id() in curr_open_orders, \
        f"expected order id {limit_order.get_id()} to be in list of open orders: \n{curr_open_orders}"
    limit_order_info = interface.get_order("BTC/USD", limit_order.get_id())
    assert limit_order_info["id"] == limit_order.get_id()

    print("Waiting for limit order status to update. Please sit tight...")

    curr_order_status = limit_order_info["status"]

    while curr_order_status == "new":
        curr_order_status = interface.get_order("BTC/USD", limit_order.get_id())["status"]
        print(f"Waiting on order status to get updated. Current order status: {curr_order_status}", end="\r")
        time.sleep(1)
    time.sleep(5)
    print("Limit order successfully closed")

    assert curr_order_status == "open", f"expected open but got {curr_order_status} (type: {type(curr_order_status)})"
    assert len(interface.get_open_orders()) == initial_num_open_orders + 1

    # cancels sell limit order
    order_id = interface.cancel_order("BTC/USD", limit_order.get_id())
    assert order_id not in test_utils.get_open_order_ids(interface.get_open_orders())
    assert len(interface.get_open_orders()) == initial_num_open_orders

    # creates sell market order
    market_order = interface.market_order("BTC/USD", "sell", 5 / interface.get_price("BTC/USD"))

    while market_order.get_status() == "open":
        print("Waiting for test market order to get accepted...", end='\r')
        time.sleep(1)

    time.sleep(5)

    print("Test market order accepted... continuing test")

    market_order_info = interface.get_order("BTC/USD", market_order.get_id())

    assert market_order.get_id() not in test_utils.get_open_order_ids(interface.get_open_orders())
    assert market_order_info["id"] == market_order.get_id()
    assert market_order_info["status"] == "closed", f"expected closed but got" + market_order_info["status"]

    # end testing ###

    print("\n --- All tests passed --- \n")


if __name__ == "__main__":

    """    
    Feel free to run the test as many times in a row as you would like for redundancy purposes
    
    net change in distribution of funds as a result of testing, between before and after the test,
    is appoximately zero
    """

    for i in range(1):
        main()
