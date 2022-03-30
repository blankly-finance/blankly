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
from dataclasses import dataclass, field

from blankly.enums import OrderStatus, OrderType, Side, PositionMode, ContractType, TimeInForce
from blankly.exchanges.interfaces.abc_base_exchange_interface import ABCBaseExchangeInterface


@dataclass
class FuturesOrder:
    symbol: str
    id: int
    size: float
    status: OrderStatus
    type: OrderType
    contract_type: ContractType
    side: Side
    position: PositionMode
    price: float
    limit_price: float
    time_in_force: TimeInForce
    response: dict = field(compare=False)
    interface: ABCBaseExchangeInterface = field(compare=False)

    def __str__(self):
        return f"""Order Parameters:
Status: {self.status}
ID: {self.id}
Symbol: {self.symbol}
Type: {self.type}
Contract Type: {self.contract_type}
Side: {self.side}
Size: {self.size}
Position: {self.position}
Price: {self.price}
Time In Force: {self.time_in_force}"""
