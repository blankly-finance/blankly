import time

import pandas as pd

import blankly.utils.time_builder
import blankly.utils.utils as utils
from blankly.exchanges.interfaces.exchange_interface import ExchangeInterface
from blankly.exchanges.orders.limit_order import LimitOrder
from blankly.exchanges.orders.market_order import MarketOrder
from blankly.exchanges.orders.stop_limit import StopLimit
from blankly.utils.exceptions import APIException, InvalidOrder

class OkexInterface(ExchangeInterface):
    def __init__(self, exchange_name, authenticated_api):
        super().__init__(exchange_name, authenticated_api, valid_resolutions=[60, 300, 900, 3600, 21600, 86400])

    def init_exchange(self):
        # This is purely an authentication check which can be disabled in settings
        fees = self.calls.get_fees()
        try:
            if fees['message'] == "Invalid API Key":
                raise LookupError("Invalid API Key. Please check if the keys were input correctly into your "
                                  "keys.json.")
        except KeyError:
            pass