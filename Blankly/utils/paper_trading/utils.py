"""
    Paper trading utilities for generating accurate paper trading responses & behaviors.
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
import secrets


def generate_coinbase_pro_id():
    # Create coinbase pro-like id
    coinbase_pro_id = secrets.token_hex(nbytes=16)
    coinbase_pro_id = coinbase_pro_id[:8] + '-' + coinbase_pro_id[8:]
    coinbase_pro_id = coinbase_pro_id[:13] + '-' + coinbase_pro_id[13:]
    coinbase_pro_id = coinbase_pro_id[:18] + '-' + coinbase_pro_id[18:]
    coinbase_pro_id = coinbase_pro_id[:23] + '-' + coinbase_pro_id[23:]

    return coinbase_pro_id