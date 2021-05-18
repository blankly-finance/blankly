"""
    Class to carry out orders
    Copyright (C) 2021  Emerson Dove, Brandon Fan

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


class Order:
    """Order Type"""
    def __init__(self, order_type, side, size, price=None):
        if order_type not in ['market', 'limit']:
            raise ValueError("Order types can only be of type ['market', 'limit'], but was given: {}".format(order_type))
        self.type = order_type
        if side not in ['buy', 'sell']:
                raise ValueError("Order side can only be of type ['buy', 'sell'], but was given: {}".format(order_type))
        self.side = side
        if self.size <= 0:
            raise ValueError("Size must be greater than zero, but was given: {}".format(size))
        if self.type == 'limit' and price == None:
            raise ValueError("Limit orders require a price but None was given")

        if price <= 0:
            raise ValueError("Price must be greater than zero but was given: {}".format(price))

        self.price = price

