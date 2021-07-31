"""
    Class for allowing easy user reporting to external processes
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

from typing import Any

from blankly.deployment.server import Connection


class Reporter:
    def __init__(self, connection: Connection):
        self.connection = connection
        self.__macros = {}

    def export_macro(self, var: Any, name: str, description: str = None):
        """
        Create a variable that can be updated by external processes
        All strings must be in ascii characters

        Args:
            var: Any variable that can represented in a string (ex: float, str, int)
            name: The name of the macro
            description (optional): A longer description for use in GUIs or other areas where context is important
        """
        var_id = id(var)
        format_message = self.connection.format_message('macro', id=var_id, name=name, description=description,
                                                        type=type(var))
        self.connection.send(format_message)
        self.__macros[var_id] = var

    def update_macro(self, var):
        return self.__macros[id(var)]
