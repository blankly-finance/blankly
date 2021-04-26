"""
    Websocket feeds need to be modular due to the subscription methods, this provides dynamic management.
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

import time


def switch_type(stream):
    if stream == "trade":
        return trade


def trade(message):
    return str(message["E"]) + "," + str(time.time()) + "," + message["e"] + "," + message["s"] + "," + \
           str(message["t"]) + "," + message["p"] + "," + message["q"] + "," + str(message["b"]) + "," + \
           str(message["a"]) + "," + str(message["T"]) + "," + str(message["m"]) + "\n"
