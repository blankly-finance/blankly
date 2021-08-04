"""
    Class for defining headers for deployment infrastructure
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


class Reporter:
    def __init__(self):
        self.__live_vars = {}
        pass

    def export_live_var(self, var: Any, name: str, description: str = None):
        """
        Create a variable that can be updated by external processes
        All strings must be in ascii characters

        Args:
            var: Any variable that can represented in a string (ex: float, str, int)
            name: The name of the live_var
            description (optional): A longer description for use in GUIs or other areas where context is important
        """
        self.__live_vars[id(var)] = var

    def update_live_var(self, var):
        """
        Get the variable as with any changes that may have occured

        Args:
            var: The variable that was exported initially
        """
        return self.__live_vars[id(var)]
