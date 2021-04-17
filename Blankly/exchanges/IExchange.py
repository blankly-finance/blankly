"""
    Interface for exchange objects.
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


class IExchange(abc.ABC):
    """
    Functions required for easy interaction with the GUI/main
    """

    @abc.abstractmethod
    def append_model(self, model, coin, args):
        pass

    @abc.abstractmethod
    def get_model(self, coin):
        pass

    @abc.abstractmethod
    def get_full_state(self, currency):
        pass

    @abc.abstractmethod
    def get_model_state(self, currency):
        pass

    @abc.abstractmethod
    def get_currency_state(self, currency):
        pass

    def get_exchange_state(self):
        pass
