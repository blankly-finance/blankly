"""
    Base Order class
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
from blankly.enums import OrderStatus, OrderType, Side, PositionMode, ContractType, TimeInForce


class FuturesOrder:
    response: dict

    symbol: str
    id: int
    created_at: float
    size: float
    status: OrderStatus
    type: OrderType
    contract_type: ContractType
    side: Side
    position: PositionMode
    price: float
    time_in_force: TimeInForce

    def __init__(self, symbol: str, id: int, created_at: float, size: float,
                 status: OrderStatus, type: OrderType,
                 contract_type: ContractType, side: Side,
                 position: PositionMode, price: float,
                 time_in_force: TimeInForce, response, interface):
        self.response = response
        self.interface = interface

        self.symbol = symbol
        self.id = id
        self.created_at = created_at
        self.size = size
        self.status = status
        self.type = type
        self.contract_type = contract_type
        self.side = side
        self.position = position
        self.price = price
        self.time_in_force = time_in_force

    def __str__(self):
        return f"""Order Parameters:
Status: {self.status}
ID: {self.id}
Symbol: {self.symbol}
Purchase Time: {self.created_at}
Type: {self.type}
Contract Type: {self.contract_type}
Side: {self.side}
Size: {self.size}
Position: {self.position}
Price: {self.price}
Time In Force: {self.time_in_force}"""
