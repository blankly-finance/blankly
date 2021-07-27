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

import copy

import blankly.exchanges.interfaces.paper_trade.local_account.local_account as local_account
import blankly.utils.utils as utils
from blankly.utils.exceptions import InvalidOrder


def trade_local(symbol, side, base_delta, quote_delta, quote_resolution, base_resolution) -> None:
    """
    Trade on the local & static account

    Args:
        symbol (string): Pair such as 'BTC-USD'
        side (string): Purchase side such as 'buy' or 'sell' (currently unused but required)
        base_delta (float): A number specifying the change in base currency, such as -2.4 BTC by selling or
         +1.2 BTC by buying
        quote_delta (float): Similar to the base_delta - a number specifying the change in quote currency, such as
         -20.12 USD for buying or +103.21 USD for selling
    """

    # Extract the base and quote pairs of the currency
    base = utils.get_base_asset(symbol)
    quote = utils.get_quote_asset(symbol)

    # Push these abstracted deltas to the local account
    try:
        local_account.account[base]['available'] = utils.trunc(local_account.account[base]['available'] + base_delta,
                                                               base_resolution)
    except KeyError:
        raise KeyError("Base currency specified not found in local account")

    try:
        local_account.account[quote]['available'] = utils.trunc(local_account.account[quote]['available'] + quote_delta,
                                                                quote_resolution)
    except KeyError:
        raise KeyError("Quote currency specified not found in local account")


def init_local_account(currencies: dict) -> None:
    """
    Create the local account to paper trade with.

    Args:
        currencies: (dict) with key/value pairs such as {'BTC': {'available: 2.3, 'hold': 0}}
    """
    local_account.account = currencies


def test_trade(currency_pair, side, qty, quote_price, quote_resolution, base_resolution) -> bool:
    """
    Test a paper trade to see if you have the funds

    Args:
        currency_pair (string): Pair such as 'BTC-USD'
        side (string): Purchase side such as 'buy' or 'sell' (currently unused but required)
        qty (float): Amount to buy of the base currency ex: (2.3 BTC of BTC-USD)
        quote_price (float): Price of the base currency in the currency pair - (1 BTC is valued at 40,245 in BTC-USD)
    """
    if side == 'buy':
        quote = utils.get_quote_asset(currency_pair)
        account = local_account.account[quote]
        current_funds = utils.trunc(account['available'], quote_resolution)
        purchase_funds = utils.trunc(quote_price * qty, quote_resolution)

        # If you have more funds than the purchase requires then return true
        if current_funds >= purchase_funds:
            return True
        else:
            raise InvalidOrder("Insufficient funds. Available:" +
                               str(current_funds) +
                               " hold: " +
                               str(account['hold']) +
                               " requested: " +
                               str(qty) + ".")

    elif side == 'sell':
        base = utils.get_base_asset(currency_pair)
        account = local_account.account[base]
        current_base = utils.trunc(account['available'], base_resolution)

        # If you have more base than the sell requires then return true
        if current_base >= qty:
            return True
        else:
            raise InvalidOrder("Not enough base currency. Available: " +
                               str(current_base) +
                               ". hold: " +
                               str(account['hold']) +
                               ". requested: " +
                               str(qty) + ".")

    else:
        raise LookupError("Invalid purchase side")


def get_accounts() -> utils.AttributeDict:
    """
    Get the paper trading local account
    """
    return copy.deepcopy(utils.AttributeDict(local_account.account))


def get_account(asset_id) -> utils.AttributeDict:
    """
    Get a single account under an asset id
    """
    return copy.deepcopy(utils.AttributeDict(local_account.account[asset_id]))


def update_available(asset_id, new_value):
    local_account.account[asset_id]['available'] = new_value


def update_hold(asset_id, new_value):
    local_account.account[asset_id]['hold'] = new_value
