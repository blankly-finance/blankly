"""
    Interface for ticker objects.
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


class ABCExchangeWebsocket(abc.ABC):
    """
    Each of these functions are required to be implemented for interaction with the ticker manager class.
    """

    @abc.abstractmethod
    def is_websocket_open(self):
        pass

    @abc.abstractmethod
    def append_callback(self, obj):
        pass

    @abc.abstractmethod
    def get_most_recent_tick(self):
        pass

    @abc.abstractmethod
    def get_most_recent_time(self):
        pass

    @abc.abstractmethod
    def get_time_feed(self):
        pass

    @abc.abstractmethod
    def get_feed(self):
        pass

    @abc.abstractmethod
    def get_response(self):
        pass

    @abc.abstractmethod
    def close_websocket(self):
        pass

    @abc.abstractmethod
    def restart_ticker(self):
        pass
