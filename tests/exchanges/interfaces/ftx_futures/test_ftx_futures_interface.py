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

from blankly.futures import FTXFutures
from pathlib import Path
from typing import List

from blankly.exchanges.interfaces.ftx_futures.ftx_futures_interface import FTXFuturesInterface


def ftx_futures_interface() -> FTXFuturesInterface:
    keys_file_path = Path("../../../config/keys.json").resolve()
    settings_file_path = Path("../../../config/settings.json").resolve()

    ftx_futures = FTXFutures(keys_path=keys_file_path,
                      preferences_path=settings_file_path,
                      portfolio_name='example-portfolio')

    # auth_obj = FTXAuth(str(keys_file_path), "Main Account")
    # _, ftx_futures_interface = DirectCallsFactory.create("ftx", auth_obj, str(settings_file_path))
    return ftx_futures.interface


"""
cancels ALL open orders and distributes funds for testing purposes

pass command line argument reset to activate

use with extreme caution

"""


def reset(ftx_futures_interface: FTXFuturesInterface):
    validation = input(
        "Continuing with this test will cancel ALL existing open orders and redistribute funds for testing purposes. "
        "Continue (Y/n)? ")
    if validation.lower() != "y":
        print("aborting test")
        quit()

    for order in ftx_futures_interface.get_open_orders():
        ftx_futures_interface.cancel_order("BTC/USD", order["id"])


def main():
    interface: FTXFuturesInterface = ftx_futures_interface()

    # validation = input(
    #     "To complete this test properly, you should have around $10 in USD in your FTX account.\nThis test will "
    #     "involve the conversion of no more than $10 to BTC.\nDo not have any trades going on while completing this "
    #     "test.\nContinue (Y/n)? ")
    # if validation.lower() != "y":
    #     quit()

    # if len(sys.argv) == 2:
    #     if sys.argv[1] == "reset":
    #         reset(interface)
    #     else:
    #         print("Invalid command line argument. Aborting")

    # start testing ###
    print(interface.history('BTC-PERP'))

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
