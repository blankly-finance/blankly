"""
    Limit Order
    Copyright (C) 2022 Matias Kotlik

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
from blankly.enums import TimeInForce
from blankly.exchanges.orders.futures.futures_order import FuturesOrder


class FuturesLimitOrder(FuturesOrder):
    needed = [*FuturesOrder.needed, ['time_in_force', TimeInForce]]

    def __init__(self, response, order, interface):
        super().__init__(response, order, interface)

    def get_time_in_force(self) -> TimeInForce:
        return TimeInForce(self.response['time_in_force'])

    def __str__(self):
        return super().__str__() + f"""Limit Order Parameters:
Time In Force: {self.get_time_in_force()}"""
