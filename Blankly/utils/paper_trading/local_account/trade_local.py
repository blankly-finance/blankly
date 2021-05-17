"""
    Local trading definition.
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
import Blankly.utils.paper_trading.local_account.local_account as local_account


def trade_local(currency, side, base_delta, quote_delta):
    if side == "sell":
        pass
    elif side == "buy":
        pass
    else:
        raise LookupError("Invalid purchase side")


def init_local_account(currencies):
    """
    Create the local account to paper trade with.

    Args:
        currencies: (dict) with key/value pairs such as {'BTC': 2.3, 'USD': 4352, 'XLM': 32}
    """
    local_account.account = currencies

