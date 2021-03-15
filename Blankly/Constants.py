"""
    Definitions for constants used in the software.
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

""" BTC """
MINIMUM_BUY_SELL = .001
CURRENT_HIGHEST_USD = 42000

""" Coinbase """
# This is currently set to the actual fee rate, sometimes .0002 (.02%) is added as padding.
PRETEND_FEE_RATE = .005

# Actual fee rates
TAKER_FEE_RATE = .005
MAKER_FEE_RATE = .005

""" Margins """
# This is used with the fee rate. This allows a guaranteed profit if it reaches past fees and this extra rate
SELL_MIN = .002

""" Settings """
EMERGENCY_SELL_SAMPLE = 10
