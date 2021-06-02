"""
    Class to pass in the current Strategy State
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


from Blankly.utils.utils import AttributeDict
from Blankly import Interface
from Blankly.strategy.strategy_base import Strategy


class StrategyState:
    """Strategy State"""
    def __init__(self, strategy: Strategy, interface: Interface, variables: AttributeDict, resolution: str = None):
        self.strategy = strategy
        self.interface = interface
        self.variables = variables
        self.resolution = resolution

