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


class FuturesOrder:
    needed = [["symbol", str], ["id", str], ["created_at", float],
              ["funds", float], ["status", str], ["type", str],
              ["contract_type", str], ["side", str], ["position", str],
              ["price", float]]

    def __init__(self, response, order, interface):
        self.response = response
        self.order = order
        self.interface = interface

    def __str__(self):
        return f"""General Order Parameters:
Status: {self.get_status()}
ID: {self.get_id()}
Symbol: {self.get_asset_id()}
Purchase Time: {self.get_purchase_time()}
Type: {self.get_type()}
Contract Type: {self.get_contract_type()}
Side: {self.get_side()}
Size: {self.get_size()}
Position: {self.get_position()}
Price: {self.get_price()}"""

    def get_response(self) -> dict:
        return self.response

    def get_id(self) -> str:
        return self.response['id']

    def get_asset_id(self) -> str:
        return self.response['symbol']

    def get_purchase_time(self) -> float:
        return self.response['created_at']

    def get_status(self) -> str:
        return self.interface.get_order(self.order['symbol'],
                                        self.get_id())['status']

    def get_type(self) -> str:
        return self.response['type']

    def get_side(self) -> str:
        return self.response['side']

    def get_size(self) -> float:
        return self.response['size']

    def get_contract_type(self) -> str:
        return self.response['contract_type']

    def get_position(self):
        return self.response['position']

    def get_price(self):
        return self.response['price']
