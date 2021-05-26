"""
    Backtesting controller for paper trading interface
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
from Blankly.exchanges.Paper_Trade.Paper_Trade_Interface import PaperTradeInterface

"""
This is a format draft for multi-equity backtesting
"""
def get_blank_settings():
    return {
        'price_event': [{
                'function': None,  # Run interval in seconds
                'interval': 0.0,  # Run interval in seconds
                'price_data': None  # Price data for this specific function
            }],
        'orderbook_event': [{
            'function': None,  # Run interval in seconds
            'interval': 0.0,  # Run interval in seconds
            'price_data': None,
            'orderbook_data': None,
            }],
        'price_dictionary': None,  # Set a global price dictionary for all functions to use

        'interval_enabled': {  # Choose between passing in a price dictionary or a
            # linear list with internally modified time
            'enabled': True  # True will mean interval, which means price data should be lists
        }
    }


class BackTestController:
    def __init__(self, paper_trade_interface: PaperTradeInterface, settings: dict):
        self.paper_trade_interface = paper_trade_interface
        self.settings = settings
        self.backtesting = False
        self.current_time = 0

    def run(self):
        # fix thise to be the first in the price array
        self.current_time = None
        self.backtesting = True


        self.backtesting = False