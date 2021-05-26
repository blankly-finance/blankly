"""
    Wrapper code for creating
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
import time


class BacktestingWrapper:
    def __init__(self):
        self.backtesting = False
        self.time = None
        self.prices = {}

    def set_backtesting(self, status: bool):
        self.backtesting = status

    def push_time(self, new_time):
        self.time = new_time

    def push_price(self, asset_id, new_price):
        self.prices[asset_id] = new_price

    def get_backtesting_price(self, asset_id):
        return self.prices[asset_id]

    def time(self):
        if self.backtesting:
            return self.time
        else:
            return time.time()
