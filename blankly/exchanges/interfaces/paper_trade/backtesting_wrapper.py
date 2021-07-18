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
        self.frame = {
            'prices': {},
            'time': 0
        }

    def set_backtesting(self, status: bool):
        self.backtesting = status

    def receive_time(self, new_time):
        self.frame['time'] = new_time

    def receive_price(self, asset_id, new_price):
        self.frame['prices'][asset_id] = new_price

    """
    Override functions for manipulating backtesting
    """

    def get_backtesting_price(self, asset_id):
        try:
            return self.frame['prices'][asset_id]
        except KeyError:
            raise KeyError("Price not found in recent frame")

    def time(self):
        if self.backtesting:
            return self.frame['time']
        else:
            return time.time()
