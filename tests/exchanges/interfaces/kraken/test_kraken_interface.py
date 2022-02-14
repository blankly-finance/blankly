# """
#
# ATTENTION:
# Kraken has NO sandbox mode, these are methods specifically designed
# to test interface methods which interact with LIVE orders, and
# move REAL funds. It is not recommended that you run these tests.
# They must be executed individually and with great caution. Blankly
# is not responsible for losses incurred by improper use of this test.
#
# How do we test methods which affect live funds?
#
# There are 5 main methods that need to be tested which involve
# using live funds
#
# 1. get_open_orders()
# 2. market_order()
# 3. limit_order()
# 4. cancel_order
#
# We test these by creating a series of assertations that can only
# pass if everything works properly.
#
# """
#
#
# import time
# import sys
# from blankly.exchanges.orders.limit_order import LimitOrder
# from blankly.utils import utils
# from pathlib import Path
# from typing import List
#
# from blankly.exchanges.interfaces.kraken.kraken_auth import KrakenAuth
# from blankly.exchanges.interfaces.kraken.kraken_interface import KrakenInterface
# from blankly.exchanges.interfaces.direct_calls_factory import DirectCallsFactory
# import test_kraken_interface_utils as test_utils
#
#
# 
# def kraken_interface() -> KrakenInterface:
#     keys_file_path = Path("tests/config/keys.json").resolve()
#     settings_file_path = Path("tests/config/settings.json").resolve()
#
#     auth_obj = KrakenAuth(str(keys_file_path), "default")
#     _, kraken_interface = DirectCallsFactory.create("kraken", auth_obj, str(settings_file_path))
#     return kraken_interface
#
# """
# cancels ALL open orders and distributes funds for testing purposes
#
# pass command line argument reset to activate
#
# use with extreme caution
#
# """
# def reset(kraken_interface: KrakenInterface):
#     validation = input("Continuing with this test will cancel ALL existing open orders and redistribute funds for testing purposes. Continue (Y/n)? ")
#     if validation.lower() != "y":
#         print("aborting test")
#         quit()
#
#     for order in kraken_interface.get_open_orders():
#         kraken_interface.cancel_order("BTC-USD", order["id"])
#
#
# def main():
#
#     interface: KrakenInterface = kraken_interface()
#
#     validation = input("To complete this test properly, you should have around $10 in USD in your Kraken account.\nThis test will involve the conversion of no more than $10 to BTC.\nDo not have any trades going on while completing this test.\nContinue (Y/n)? ")
#     if validation.lower() != "y":
#         quit()
#
#     if len(sys.argv) == 2:
#         if sys.argv[1] == "reset":
#             reset(interface)
#         else:
#             print("Invalid command line argument. Aborting")
#
#     ### start testing ###
#
#
#     initial_num_open_orders = len(interface.get_open_orders())
#
#     #creates a buy limit order unlikely to be fulfilled (buying a bitcoin for $5)
#     limit_order = interface.limit_order("BTC-USD", "buy", 1, 5)
#     assert len(interface.get_open_orders()) == 1 + initial_num_open_orders, f"expected {1 + initial_num_open_orders} but got {len(interface.get_open_orders())}"
#     assert limit_order.get_status()['status'] == "new" or limit_order.get_status()['status'] == "open", f"expected open but got {limit_order.get_status()['status']} of type {type(limit_order.get_status()['status'])}"
#
#     open_order_ids: List[int] = test_utils.get_open_order_ids(interface.get_open_orders())
#     limit_order_id = int(limit_order.get_id())
#     assert limit_order_id in open_order_ids, f"id {limit_order_id} (type: {type(limit_order_id)}) not in list {open_order_ids} (type: {type(open_order_ids)})"
#
#     #cancels the open limit order
#     order_id = int(interface.cancel_order("BTC-USD", limit_order.get_id()))
#
#     curr_num_open_orders = len(interface.get_open_orders())
#     assert curr_num_open_orders == initial_num_open_orders, f"expected {initial_num_open_orders} open orders, but got {curr_num_open_orders}\nopen order list:\n{interface.get_open_orders()}"
#     assert order_id not in test_utils.get_open_order_ids(interface.get_open_orders())
#
#     #creates a buy market order for $5 worth of bitcoin
#     market_order = interface.market_order("BTC-USD", "buy", 5 / interface.get_price("BTC-USD"))
#
#     while market_order.get_status() == "open":
#         print("Waiting for test market order to get accepted...", end = '\r')
#         time.sleep(1)
#
#     print("Test market order accepted... continuing test")
#
#     market_order_info = interface.get_order("BTC-USD", market_order.get_id())
#
#     assert market_order.get_id() not in test_utils.get_open_order_ids(interface.get_open_orders())
#     assert market_order_info["id"] == market_order.get_id()
#     market_order_status = market_order_info["status"]
#     assert market_order_status == "closed", f"expected closed, but got {market_order_status} (type: {type(market_order_status)}) \nopen orders: {interface.get_open_orders()}"
#
#     #creates a sell limit order unlikely to get fulfilled (selling $5 worth of bitcoin for $5000)
#     limit_order = interface.limit_order("BTC-USD", "sell", 5000 * (interface.get_price("BTC-USD") / 5), interface.get_price("BTC-USD") / 5)
#
#     assert limit_order.get_id() in test_utils.get_open_order_ids(interface.get_open_orders())
#     limit_order_info = interface.get_order("BTC-USD", limit_order.get_id())
#     assert limit_order_info["id"] == limit_order.get_id()
#     assert limit_order_info["status"] == "open"
#     assert len(interface.get_open_orders()) == initial_num_open_orders + 1
#
#     #cancels sell limit order
#     order_id = interface.cancel_order("BTC-USD", limit_order.get_id())
#     assert order_id not in test_utils.get_open_order_ids(interface.get_open_orders())
#     assert len(interface.get_open_orders()) == initial_num_open_orders
#
#     #creates sell market order
#     market_order = interface.market_order("BTC-USD", "sell", 5 / interface.get_price("BTC-USD"))
#
#     while market_order.get_status() == "open":
#         print("Waiting for test market order to get accepted...", end = '\r')
#         time.sleep(1)
#
#     print("Test market order accepted... continuing test")
#
#     market_order_info = interface.get_order("BTC-USD", market_order.get_id())
#
#     assert market_order.get_id() not in test_utils.get_open_order_ids(interface.get_open_orders())
#     assert market_order_info["id"] == market_order.get_id()
#     assert market_order_info["status"] == "closed"
#
#     ### end testing ###
#
# if __name__ == "__main__":
#     main()