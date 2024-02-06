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

import blankly.utils.utils as utils
from blankly.utils.exceptions import InvalidOrder


class LocalAccount:
    def __init__(self, currencies: dict) -> None:
        """
        Create the local account to paper trade with.

        Args:
            currencies: (dict) with key/value pairs such as {'BTC': {'available: 2.3, 'hold': 0}}
        """
        # This is used for shorting. It largely corresponds with margin
        self.__granted_value = {}
        self.local_account = utils.AttributeDict(currencies)

    def override_local_account(self, currencies: dict) -> None:
        """
        After initialization, this is a setter for overriding the internal values
        """
        self.local_account = currencies

    def trade_local(self, symbol, side, base_delta, quote_delta, quote_resolution, base_resolution) -> None:
        """
        Trade on the local & static account

        Args:
            symbol (string): Pair such as 'BTC-USD'
            side (string): Purchase side such as 'buy' or 'sell' (currently unused but required)
            base_delta (float): A number specifying the change in base currency, such as -2.4 BTC by selling or
             +1.2 BTC by buying
            quote_delta (float): Similar to the base_delta - a number specifying the change in quote currency, such as
             -20.12 USD for buying or +103.21 USD for selling
            quote_resolution (int): The number of decimals that are supported for the quote
            base_resolution (int): The number of decimals that are supported for the base
        """

        # Extract the base and quote pairs of the currency
        base = utils.get_base_asset(symbol)
        quote = utils.get_quote_asset(symbol)

        # Push these abstracted deltas to the local account
        try:
            self.local_account[base]['available'] = utils.trunc(self.local_account[base]['available'] + base_delta,
                                                                base_resolution)
        except KeyError:
            raise KeyError("Base currency specified not found in local account")

        try:
            self.local_account[quote]['available'] = utils.trunc(self.local_account[quote]['available'] + quote_delta,
                                                                 quote_resolution)
        except KeyError:
            raise KeyError("Quote currency specified not found in local account")

    def test_trade(self, currency_pair, side, qty, quote_price, quote_resolution, base_resolution, shortable) -> bool:
        """
        Test a paper trade to see if you have the funds

        Args:
            currency_pair (string): Pair such as 'BTC-USD'
            side (string): Purchase side such as 'buy' or 'sell'
            qty (float): Amount to buy of the base currency ex: (2.3 BTC of BTC-USD)
            quote_price (float): Price of the base currency in the currency pair - (1 BTC is valued at 40,245 in
             BTC-USD)
        """
        # Nobody knows what's happening if it's shorting
        if shortable:
            base_asset = utils.get_base_asset(currency_pair)
            quote_asset = utils.get_quote_asset(currency_pair)
            base_account = self.local_account[base_asset]
            quote_account = self.local_account[quote_asset]

            # Initialize a granted value if not already created
            if quote_asset not in self.__granted_value:
                self.__granted_value[quote_asset] = 0

            if side == "sell":
                # Selling is the only thing that can give granted value
                target_quantity = base_account['available'] - qty

                # If they sell and its still just positive that's a valid condition
                if target_quantity > 0:
                    # print(self.__granted_value)
                    return True

                # Remember in this case if it crosses the zero line and becomes negative some positive
                #  value doesn't convert into negative, so we have to understand how much deficit we need
                if base_account['available'] > 0:
                    # This just the part of the quantity request that goes over zero
                    # Qty should be bigger in this case, so we're looking for that difference
                    size_increase_negative = qty - base_account['available']
                else:
                    # In this case because we're already negative we're increasing by this size
                    size_increase_negative = qty

                # In this case the target funds is less than zero which means we have to grant value (margin)
                negative_deficit = self.__granted_value[quote_asset] + abs(size_increase_negative * quote_price)
                margin_requested = utils.trunc(abs(size_increase_negative * quote_price), quote_resolution)
                if negative_deficit >= quote_account['available']:
                    raise InvalidOrder(f"Not enough margin to perform short - total margin available: "
                                       f"{quote_account['available']}, margin already granted: "
                                       f" {self.__granted_value[quote_asset]}, margin requested: "
                                       f"{margin_requested}")
                else:
                    # Add this on margin and allow the order
                    self.__granted_value[quote_asset] += margin_requested
                    # print(self.__granted_value)
                    return True

            elif side == "buy":
                # Buying is the only thing that can eat granted value
                target_size = base_account['available'] + qty
                requested_funds = utils.trunc(abs(qty * quote_price), quote_resolution)
                target_funds = quote_account['available'] - requested_funds

                if target_funds < 0:
                    raise InvalidOrder(f'Not enough funds to buy - available: '
                                       f'{quote_account["available"]}, requested: '
                                       f'{requested_funds}.')

                # The valid condition is if the current amount and the final amount are both greater than zero
                if (target_size >= 0) and (base_account['available'] >= 0):
                    pass
                    # print("Eating 0")
                    # print(self.__granted_value)

                if (target_size >= 0) and (base_account['available'] <= 0):
                    # This will eat a small portion of the granted value (margin)
                    self.__granted_value[quote_asset] -= utils.trunc(abs(base_account['available'] *
                                                                         quote_price), quote_resolution)
                    # print(f"Eating {utils.trunc(abs(base_account['available'] * quote_price), quote_resolution)}")
                    # print(self.__granted_value)

                if (target_size <= 0) and (base_account['available'] <= 0):
                    # This will also eat the qty increase
                    self.__granted_value[quote_asset] -= utils.trunc(abs(qty * quote_price), quote_resolution)
                    # print(f"Eating {utils.trunc(abs(qty * quote_price), quote_resolution)}")
                    # print(self.__granted_value)

                # Correct this just in case they sell for a profit
                if self.__granted_value[quote_asset] < 0:
                    self.__granted_value[quote_asset] = 0

                return True
        else:
            if side == 'buy':
                quote = utils.get_quote_asset(currency_pair)
                account = self.local_account[quote]
                current_funds = self.local_account[quote]['available']
                purchase_funds = utils.trunc(quote_price * qty, quote_resolution)

                # If you have more funds than the purchase requires then return true
                if current_funds >= purchase_funds:
                    return True
                else:
                    raise InvalidOrder("Insufficient funds. Available: " +
                                       str(current_funds) +
                                       " hold: " +
                                       str(account['hold']) +
                                       " requested: " +
                                       str(purchase_funds) + ".")

            elif side == 'sell':
                base = utils.get_base_asset(currency_pair)
                account = self.local_account[base]
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

        raise LookupError("Invalid purchase side")

    def get_accounts(self) -> utils.AttributeDict:
        """
        Get the paper trading local account
        """
        return copy.deepcopy(utils.AttributeDict(self.local_account))

    def get_account(self, asset_id) -> utils.AttributeDict:
        """
        Get a single account under an asset id
        """
        return copy.deepcopy(utils.AttributeDict(self.local_account[asset_id]))

    def update_available(self, asset_id, new_value):
        self.local_account[asset_id]['available'] = new_value

    def update_hold(self, asset_id, new_value):
        self.local_account[asset_id]['hold'] = new_value
