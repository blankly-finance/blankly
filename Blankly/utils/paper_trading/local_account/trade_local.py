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
import Blankly.utils.utils as utils


def trade_local(currency_pair, side, base_delta, quote_delta) -> None:
    """
    Trade on the local & static account

    Args:
        currency_pair (string): Pair such as 'BTC-USD'
        side (string): Purchase side such as 'buy' or 'sell' (currently unused but required)
        base_delta (float): A number specifying the change in base currency, such as -2.4 BTC by selling or
         +1.2 BTC by buying
        quote_delta (float): Similar to the base_delta - a number specifying the change in quote currency, such as
         -20.12 USD for buying or +103.21 USD for selling
    """

    # Extract the base and quote pairs of the currency
    base = utils.get_base_currency(currency_pair)
    quote = utils.get_quote_currency(currency_pair)

    # Push these abstracted deltas to the local account
    try:
        local_account.account[base] = local_account.account[base] + base_delta
    except KeyError:
        raise KeyError("Base currency specified not found in local account")

    try:
        local_account.account[quote] = local_account.account[quote] + quote_delta
    except KeyError:
        raise KeyError("Quote currency specified not found in local account")


def init_local_account(currencies) -> None:
    """
    Create the local account to paper trade with.

    Args:
        currencies: (dict) with key/value pairs such as {'BTC': 2.3, 'USD': 4352, 'XLM': 32}
    """
    local_account.account = currencies


def test_trade(currency_pair, side, qty, quote_price) -> bool:
    """
    Test a paper trade to see if you have the funds

    Args:
        currency_pair (string): Pair such as 'BTC-USD'
        side (string): Purchase side such as 'buy' or 'sell' (currently unused but required)
        qty (float): Amount to buy of the base currency ex: (2.3 BTC of BTC-USD)
        quote_price (float): Price of the base currency in the currency pair - (1 BTC is valued at 40,245 in BTC-USD)
    """
    if side == 'buy':
        quote = utils.get_quote_currency(currency_pair)
        current_funds = local_account.account[quote]
        purchase_funds = quote_price * qty

        # If you have more funds than the purchase requires then return true
        return current_funds > purchase_funds

    elif side == 'sell':
        base = utils.get_base_currency(currency_pair)
        current_base = local_account.account[base]

        # If you have more base than the sell requires then return true
        return current_base > qty

    else:
        raise LookupError("Invalid purchase side")


def get_accounts() -> dict:
    """
    Get the paper trading local account
    """
    return local_account.account
