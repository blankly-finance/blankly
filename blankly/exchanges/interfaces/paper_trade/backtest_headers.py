"""
    Headers to provide a clean UI to users
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
import abc
import typing


class ABCBacktestController(abc.ABC):
    @abc.abstractmethod
    def add_prices(self, symbol: str,
                   resolution: [str, int, float],
                   to: str = None,
                   start_date: typing.Union[str, float, int] = None,
                   stop_date: typing.Union[str, float, int] = None):
        """
        Add prices directly to the backtest engine
        """
        pass

    @abc.abstractmethod
    def value_account(self):
        """
        Value your account at this time
        """
        pass
