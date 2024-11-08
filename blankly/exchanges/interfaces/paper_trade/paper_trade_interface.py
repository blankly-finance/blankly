"""
    Paper trade exchange constructed from other interfaces
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

import threading
import time
import traceback

import blankly.exchanges.interfaces.paper_trade.utils as paper_trade
import blankly.utils.utils as utils
from blankly.exchanges.interfaces.paper_trade.local_account.trade_local import LocalAccount
from blankly.exchanges.interfaces.abc_exchange_interface import ABCExchangeInterface
from blankly.exchanges.interfaces.exchange_interface import ExchangeInterface
from blankly.exchanges.interfaces.paper_trade.backtesting_wrapper import BacktestingWrapper
from blankly.exchanges.orders.limit_order import LimitOrder
from blankly.exchanges.orders.market_order import MarketOrder
from blankly.exchanges.orders.stop_loss import StopLossOrder
from blankly.exchanges.orders.take_profit import TakeProfitOrder
from blankly.utils.exceptions import APIException, InvalidOrder


class PaperTradeInterface(ExchangeInterface, BacktestingWrapper):
    def __init__(self, derived_interface: ABCExchangeInterface, initial_account_values: dict = None):
        # This paper trade orders keeps a live track of the orders
        self.paper_trade_orders = []
        # These two keep track of which limit orders and when the order finishes
        self.canceled_orders = []
        self.executed_orders = []

        # Save the market order execution details for later
        self.market_order_execution_details = []

        self.get_products_cache = None
        self.get_fees_cache = {}
        self.get_order_filter_cache = {}

        self.__run_watchdog = True

        self.__thread = None

        # Set the type of the paper trade exchange to be the same as whichever interface its derived from
        ExchangeInterface.__init__(self, derived_interface.get_exchange_type(), derived_interface)
        BacktestingWrapper.__init__(self)

        self.__local_account_cache = None
        self.__initial_account_values = initial_account_values

        # Initialize our traded assets list
        self.traded_assets = []

        # self.evaluate_traded_account_assets()

        self.__enable_shorting = self.user_preferences['settings']['alpaca']['enable_shorting']

    @property
    def local_account(self):
        if self.__local_account_cache is None:
            if self.get_exchange_type() == 'keyless':
                accounts = utils.add_all_products({}, self.get_products())
            else:
                # Write in the accounts to our local account. This involves getting the values directly from the
                # exchange
                accounts = self.calls.get_account()
            # If it's given an initial account value dictionary, write all the account values that we passed in to the
            # function to the account, then default everything else to zero.
            if self.__initial_account_values is not None:
                for i in accounts.keys():
                    if i in self.__initial_account_values.keys():
                        accounts[i] = utils.AttributeDict({
                            'available': self.__initial_account_values[i],
                            'hold': 0.0
                        })
                    else:
                        accounts[i] = utils.AttributeDict({
                            'available': 0.0,
                            'hold': 0.0
                        })

            # Initialize the local account
            self.__local_account_cache = LocalAccount(accounts)
            return self.__local_account_cache
        else:
            return self.__local_account_cache

    def evaluate_traded_account_assets(self):
        # Because alpaca has so many columns we need to optimize to perform an accurate backtest
        accounts = self.get_account()

        for i in accounts.keys():
            if (accounts[i]['available'] + accounts[i]['hold']) != 0 and i not in self.traded_assets:
                self.traded_assets.append(i)

    def backtesting_time(self):
        """
        Return the backtest time if we're backtesting, if not just return None. If it's None the caller
         assumes no backtesting. The function being overridden always returns None
        """
        # This is for the inits because it happens with both live calls and in the past
        if self.initial_time is not None and not self.backtesting:
            return self.initial_time
        # This is for the actual price loops
        if self.backtesting:
            return self.time()
        else:
            return None

    def __check_trading_assets(self, symbol: str):
        """
        Append a newly traded symbol to traded assets array. This is used to more efficiently evaluate
        which accounts need graphs

        Args:
            symbol (str): The string representing the asset
        """
        base_asset = utils.get_base_asset(symbol)
        quote_asset = utils.get_quote_asset(symbol)

        if base_asset not in self.traded_assets:
            self.traded_assets.append(base_asset)

        if quote_asset not in self.traded_assets:
            self.traded_assets.append(quote_asset)

    def init_exchange(self):
        try:
            self.calls.get_exchange_type()
        except AttributeError:
            traceback.print_exc()
            raise AttributeError("Are you passing a non-exchange object into the paper trade constructor?")

    """ Needs to be overridden here """

    def start_paper_trade_watchdog(self):
        # TODO, this process could use variable update time/websocket usage, poll `time` and a variety of settings
        #  to create a robust trading system
        # Create the watchdog for watching limit orders
        self.__thread = threading.Thread(target=self.__paper_trade_watchdog(), daemon=True)
        self.__thread.start()
        self.__run_watchdog = True

    def stop_paper_trade_watchdog(self):
        self.__run_watchdog = False

    """ Needs to be overridden here """

    def __paper_trade_watchdog(self):
        """
        Internal order watching system
        """
        while True:
            time.sleep(10)
            if not self.__run_watchdog:
                break
            self.evaluate_limits()

    @staticmethod
    def __get_decimals(number) -> int:
        return utils.count_decimals(number)

    def override_local_account(self, value_dictionary: dict):
        """
        Push a new set of initial account values to the algorithm. All values not given in the
        value dictionary that currently exist will be set to zero.

        Args:
            value_dictionary (dict): Account dictionary of format {'BTC': 2.3, 'GRT': 1.1}
        """
        current_account = self.local_account.get_accounts()
        for k, v in current_account.items():
            if k in value_dictionary.keys():
                current_account[k] = utils.AttributeDict({
                    'available': value_dictionary[k],
                    'hold': 0
                })
            else:
                current_account[k] = utils.AttributeDict({
                    'available': 0,
                    'hold': 0
                })
        self.local_account.override_local_account(current_account)

    def evaluate_limits(self):
        """
        When this is run it checks the local paper trade orders to see if any need to go through
        """
        used_currencies = []
        for i in self.paper_trade_orders:
            if i["symbol"] not in used_currencies:
                used_currencies.append(i['symbol'])
        prices = {}

        decimals_dict = {}
        # get the market limits so that we can get accurate rounding
        for i in used_currencies:
            market_limits = self.get_order_filter(i)
            decimals_dict[i] = {}
            decimals_dict[i]['quantity_decimals'] = self.__get_decimals(market_limits['limit_order']['base_increment'])
            decimals_dict[i]['quote_decimals'] = self.__get_decimals(market_limits['market_order']['quote_increment'])

        for i in used_currencies:
            prices[i] = self.get_price(i)
            if not self.backtesting:
                time.sleep(.2)

        for i in range(len(self.paper_trade_orders)):
            index = self.paper_trade_orders[i]
            """
            Coinbase pro example
            {
                "id": "d0c5340b-6d6c-49d9-b567-48c4bfca13d2",
                "price": "0.10000000",
                "size": "0.01000000",
                "product_id": "BTC-USD",
                "side": "buy",
                "stp": "dc",
                "type": "limit",
                "time_in_force": "GTC",
                "post_only": false,
                "created_at": "2016-12-08T20:02:28.53864Z",
                "fill_fees": "0.0000000000000000",
                "filled_size": "0.00000000",
                "executed_value": "0.0000000000000000",
                "status": "pending",
                "settled": false
            }
            """
            if index['type'] in ('limit', 'stop_loss') and index['status'] == 'pending':
                current_price = prices[index['symbol']]
                limit_price = index['price']

                if index['side'] == 'buy':
                    if index['price'] > current_price:
                        # Take everything off hold
                        asset_id = index['symbol']
                        quote = utils.get_quote_asset(asset_id)

                        available = self.local_account.get_account(quote)['available']
                        # Put it back into available
                        self.local_account.update_available(quote, available + (index['size'] * index['price']))

                        # Take it out of hold
                        hold = self.local_account.get_account(quote)['hold']
                        self.local_account.update_hold(quote, hold - (index['size'] * index['price']))

                        order, funds, executed_value, fill_fees, filled_size = self.evaluate_paper_trade(index,
                                                                                                         index['price'])
                        self.local_account.trade_local(symbol=index['symbol'],
                                                       side='buy',
                                                       base_delta=filled_size,  # Gain filled size after fees
                                                       quote_delta=funds * -1,  # Loose the original fund amount
                                                       base_resolution=decimals_dict[index['symbol']]
                                                       ['quantity_decimals'],
                                                       quote_resolution=decimals_dict[index['symbol']]
                                                       ['quote_decimals'])
                        order['status'] = 'done'
                        order['settled'] = 'true'

                        # Add this to the executed orders
                        self.executed_orders.append({
                            'id': index['id'],
                            'executed_time': self.time(),
                        })

                        self.paper_trade_orders[i] = order
                elif index['side'] == 'sell':
                    if limit_price < current_price and index['type'] == 'limit' \
                            or current_price <= limit_price and index['type'] == 'stop_loss':
                        # Take everything off hold

                        asset_id = index['symbol']
                        base = utils.get_base_asset(asset_id)

                        available = self.local_account.get_account(base)['available']
                        # Put it back into available
                        self.local_account.update_available(base, available + index['size'])

                        # Remove it from hold
                        hold = self.local_account.get_account(base)['hold']
                        self.local_account.update_hold(base, hold - index['size'])

                        order, funds, executed_value, fill_fees, filled_size = self.evaluate_paper_trade(index,
                                                                                                         index['price'])
                        self.local_account.trade_local(symbol=index['symbol'],
                                                       side='sell',
                                                       base_delta=float(order['size'] * - 1),
                                                       # Loose size before any fees
                                                       quote_delta=executed_value,  # Executed value after fees
                                                       base_resolution=decimals_dict[index['symbol']]
                                                       ['quantity_decimals'],
                                                       quote_resolution=decimals_dict[index['symbol']]['quote_decimals']
                                                       )
                        order['status'] = 'done'
                        order['settled'] = 'true'

                        # Add this to the executed orders
                        self.executed_orders.append({
                            'id': index['id'],
                            'executed_time': self.time(),
                        })

                        self.paper_trade_orders[i] = order

    def evaluate_paper_trade(self, order, current_price):
        """
        This calculates fees & evaluates accurate value
        Args:
            order (dict): Order dictionary to derive the order attributes
            current_price (float): The current price of the currency pair the limit order was created on
        """
        funds = order['size'] * current_price
        executed_value = funds - funds * float((self.get_fees(order['symbol'])["maker_fee_rate"]))
        fill_fees = funds * float((self.get_fees(order['symbol'])["maker_fee_rate"]))
        fill_size = order['size'] - order['size'] * float((self.get_fees(order['symbol'])["maker_fee_rate"]))

        return order, funds, executed_value, fill_fees, fill_size

    @utils.enforce_base_asset
    def get_account(self, symbol=None) -> utils.AttributeDict:
        if symbol is None:
            return self.local_account.get_accounts()
        else:
            # This is a super call in all other interfaces. This apparently doesn't work here because of multiple
            # inheritance
            symbol = utils.get_base_asset(symbol)
            try:
                return self.local_account.get_account(symbol)
            except KeyError:
                if self.backtesting:
                    raise KeyError("Symbol not found. This can be caused by an invalid quote currency "
                                   "in backtest.json.")
                else:
                    raise KeyError("Symbol not found.")

    def take_profit_order(self, symbol: str, price: float, size: float) -> TakeProfitOrder:
        # we don't simulate partial fills, this is the same as take_profit
        order = self.limit_order(symbol, 'sell', price, size)
        return TakeProfitOrder(order._LimitOrder__order, order._LimitOrder__response, order.Interface)

    def stop_loss_order(self, symbol: str, price: float, size: float):
        return self.limit_order(symbol, 'sell', price, size, stop_loss=True)

    def market_order(self, symbol, side, size) -> MarketOrder:
        if not self.backtesting:
            print("Paper Trading...")
        needed = self.needed['market_order']
        creation_time = self.time()
        price = self.get_price(symbol)
        funds = price*size

        market_limits = self.get_order_filter(symbol)

        min_size = market_limits['market_order']["base_min_size"]

        max_size = market_limits['market_order']["base_max_size"]

        if size < min_size:
            raise InvalidOrder(f"Size is too small. Minimum is: {min_size}. You requested {size}.")

        if size > max_size:
            raise InvalidOrder(f"Size is too large. Maximum is: {max_size}. You requested {size}.")

        base_increment = market_limits['market_order']['base_increment']
        base_decimals = self.__get_decimals(base_increment)

        # Test if funds has more decimals than the increment. The increment is the maximum resolution of the quote.
        if self.should_auto_trunc:
            size = utils.trunc(size, base_decimals)
        elif self.__get_decimals(size) > base_decimals:
            raise InvalidOrder("Size resolution is too high, the highest resolution allowed for this symbol is: " +
                               str(base_increment) + ". You specified " + str(size) +
                               ". Try using blankly.trunc(size, decimal_number) to match the exchange resolution.")

        if self.get_exchange_type() == 'alpaca':
            # This could break, but there appears that 10 decimals is about right for alpaca
            quantity_decimals = 10
            shortable = market_limits['exchange_specific']['shortable']
        else:
            shortable = False
            quantity_decimals = self.__get_decimals(market_limits['limit_order']['base_increment'])

        order = {
            'size': size,
            'side': side,
            'symbol': symbol,
            'type': 'market'
        }
        qty = size

        # Test the purchase
        self.local_account.test_trade(symbol, side, qty, price, market_limits['market_order']["quote_increment"],
                                      quantity_decimals, (shortable and self.__enable_shorting))
        # Create coinbase pro-like id
        coinbase_pro_id = paper_trade.generate_coinbase_pro_id()
        # TODO the force typing here isn't strictly necessary because its run int the isolate_specific anyway
        response = {
            'symbol': str(symbol),
            'id': str(coinbase_pro_id),
            'created_at': str(creation_time),
            # 'funds': str(utils.trunc(size - size * float((self.__exchange_properties["taker_fee_rate"])),
            #                          base_decimals)),
            'size': str(size),
            'status': 'done',
            'type': 'market',
            'side': str(side),
            # 'specified_funds': str(funds),
            # 'post_only': 'false',
            # 'done_at': str(self.time()),
            # 'done_reason': 'filled',
            # 'fill_fees': str(utils.trunc(funds * float((self.__exchange_properties["maker_fee_rate"])),
            #                              quote_decimals)),
            # 'filled_size': str(utils.trunc(funds - funds *
            #                                float((self.__exchange_properties["maker_fee_rate"])) / price,
            #                                quantity_decimals)),
            # 'executed_value': str(utils.trunc(funds - funds * float((self.__exchange_properties["maker_fee_rate"])),
            #                                   quote_decimals)),
            # 'settled': 'true'
            'exchange_specific': {}
        }
        response = utils.isolate_specific(needed, response)
        self.paper_trade_orders.append(response)
        # Identify the trade also by exchange
        if self.backtesting:
            self.paper_trade_orders[-1]['exchange'] = self.get_exchange_type()

        if side == "buy":
            self.local_account.trade_local(symbol=symbol,
                                           side=side,
                                           base_delta=utils.trunc(qty -
                                                                  qty *
                                                                  float((self.get_fees(symbol)["taker_fee_rate"])),
                                                                  quantity_decimals),
                                           # Gain filled size after fees
                                           quote_delta=utils.trunc(funds * -1,
                                                                   base_decimals),  # Loose the original fund amount
                                           quote_resolution=base_decimals, base_resolution=quantity_decimals)
        elif side == "sell":
            self.local_account.trade_local(symbol=symbol,
                                           side=side,
                                           base_delta=utils.trunc(float(qty * -1), quantity_decimals),
                                           # Loose size before any fees
                                           quote_delta=utils.trunc(funds - funds *
                                                                   float((self.get_fees(symbol)[
                                                                       "taker_fee_rate"])),
                                                                   base_decimals),  # Gain executed value after fees
                                           quote_resolution=base_decimals, base_resolution=quantity_decimals)
        else:
            raise APIException("Invalid trade side: " + str(side))

        self.__check_trading_assets(symbol)

        self.market_order_execution_details.append({
            'id': response['id'],
            'executed_price': price
        })
        return MarketOrder(order, response, self)

    def limit_order(self, symbol, side, price, size, stop_loss=False) -> LimitOrder:
        """
        Used for buying or selling limit orders
        Args:
            symbol: currency to buy
            side: buy/sell
            price: price to set limit order
            size: amount of currency (like BTC) for the limit to be valued
        """
        needed = self.needed['limit_order']
        """
        {
            "id": "d0c5340b-6d6c-49d9-b567-48c4bfca13d2",
            "price": "0.10000000",
            "size": "0.01000000",
            "product_id": "BTC-USD",
            "side": "buy",
            "stp": "dc",
            "type": "limit",
            "time_in_force": "GTC",
            "post_only": false,
            "created_at": "2016-12-08T20:02:28.53864Z",
            "fill_fees": "0.0000000000000000",
            "filled_size": "0.00000000",
            "executed_value": "0.0000000000000000",
            "status": "pending",
            "settled": false
        }
        """
        order = {
            'size': size,
            'side': side,
            'price': price,
            'symbol': symbol,
            'type': 'stop_loss' if stop_loss else 'limit'
        }
        creation_time = self.time()

        order_filter = self.get_order_filter(symbol)

        min_base = float(order_filter['limit_order']["base_min_size"])
        max_base = float(order_filter['limit_order']["base_max_size"])

        if size < min_base:
            raise InvalidOrder("Order quantity is too small. Minimum is: " + str(min_base))

        if size > max_base:
            raise InvalidOrder("Order quantity is too large. Maximum is: " + str(max_base))

        min_price = float(order_filter['limit_order']["min_price"])
        max_price = float(order_filter['limit_order']["max_price"])

        if price < min_price:
            raise InvalidOrder("Limit price is too small. Minimum is: " + str(min_price))

        if price > max_price:
            raise InvalidOrder("Limit price is too large. Maximum is: " + str(max_price))

        # Check if the passed parameters are more accurate than either of the max base resolution or max price
        # resolution
        price_increment = order_filter['limit_order']['price_increment']
        price_increment_decimals = self.__get_decimals(price_increment)

        if self.should_auto_trunc:
            price = utils.trunc(price, price_increment_decimals)
        elif self.__get_decimals(price) > price_increment_decimals:
            raise InvalidOrder("Fund resolution is too high, minimum resolution is: " + str(price_increment) +
                               ". Try using blankly.trunc(size, decimal_number) to match the exchange resolution.")

        base_increment = order_filter['limit_order']['base_increment']
        base_decimals = self.__get_decimals(base_increment)

        if self.should_auto_trunc:
            size = utils.trunc(size, base_decimals)
        elif self.__get_decimals(size) > base_decimals:
            raise InvalidOrder("Fund resolution is too high, minimum resolution is: " + str(base_increment) +
                               '. Try using blankly.trunc(size, decimal_number) to match the exchange resolution.')

        order = {
            'size': size,
            'side': side,
            'price': price,
            'symbol': symbol,
            'type': 'limit'
        }

        # Test the trade
        self.local_account.test_trade(symbol, side, size, price, quote_resolution=price_increment_decimals,
                                      base_resolution=base_decimals, shortable=False)

        # Create coinbase pro-like id
        coinbase_pro_id = paper_trade.generate_coinbase_pro_id()
        # TODO the response fills in the exchange specific tags into the base dictionary. This is
        #  useful but really shouldn't be included. We actually really need executed value as a
        #  universally included key.
        response = {
            'symbol': str(symbol),
            'id': str(coinbase_pro_id),
            'created_at': str(creation_time),
            'price': str(price),
            'size': str(size),
            'status': 'pending',
            "time_in_force": "GTC",
            'type': 'stop_loss' if stop_loss else 'limit',
            'side': str(side),
            # 'stp': 'dc',
            # 'post_only': 'false',
            # "fill_fees": "0.0000000000000000",
            # "filled_size": "0.00000000",
            # "executed_value": "0.0000000000000000",
            # 'settled': 'false'
            'exchange_specific': {}
        }
        response = utils.isolate_specific(needed, response)
        self.paper_trade_orders.append(response)
        # Identify the trade also by exchange
        self.paper_trade_orders[-1]['exchange'] = self.get_exchange_type()

        base = utils.get_base_asset(symbol)
        quote = utils.get_quote_asset(symbol)

        if side == "buy":
            available = self.local_account.get_account(quote)['available']
            # Loose the funds when buying
            self.local_account.update_available(quote, available - (size * price))

            # Gain the funds on hold when buying
            hold = self.local_account.get_account(quote)['hold']
            self.local_account.update_hold(quote, hold + (size * price))
        elif side == "sell":
            available = self.local_account.get_account(base)['available']
            # Loose the size when selling
            self.local_account.update_available(base, available - size)

            # Gain size on hold when selling
            hold = self.local_account.get_account(base)['hold']
            self.local_account.update_hold(base, hold + size)
        else:
            raise APIException(f"Invalid side {side}")
        # TODO this is super stinky but refactoring this code is even stinkier
        return StopLossOrder(order, response, self) if stop_loss else LimitOrder(order, response, self)

    def cancel_order(self, symbol, order_id) -> dict:
        """
        This block could potentially work for both exchanges
        """
        del symbol
        order_index = None
        for i in range(len(self.paper_trade_orders)):
            index = self.paper_trade_orders[i]
            if index['status'] == 'pending' and index['id'] == order_id:
                order_index = i
                break

        if order_index is not None:
            # Now that we found it make sure that we move the funds back on available
            order = self.paper_trade_orders[order_index]
            side = order['side']
            size = order['size']
            symbol = order['symbol']
            price = order['price']
            base_asset = utils.get_base_asset(symbol)
            quote_asset = utils.get_quote_asset(symbol)

            if side == 'buy':
                # When you cancel on the buy side you get those funds back in available
                available = self.local_account.get_account(quote_asset)['available']
                self.local_account.update_available(quote_asset, available + (size * price))

                # And loose them on hold
                hold = self.local_account.get_account(quote_asset)['hold']
                self.local_account.update_hold(quote_asset, hold - (size * price))
            elif side == 'sell':
                # Canceling a sell you gain the size back into available
                available = self.local_account.get_account(base_asset)['available']
                self.local_account.update_available(base_asset, available + size)

                # And you loose it in the hold
                hold = self.local_account.get_account(base_asset)['hold']
                self.local_account.update_hold(base_asset, hold - size)

            # This saves the order
            order_id = order['id']
            # Make sure to save this as a canceled order just before closing it
            # Make sure to write in the time also
            self.canceled_orders.append({
                'id': self.paper_trade_orders[order_index]['id'],
                'canceled_time': self.time()
            })

            del self.paper_trade_orders[order_index]
            return {"order_id": order_id}
        else:
            raise APIException("Order ID not found.")

    def get_open_orders(self, symbol=None):
        open_orders = []
        for i in self.paper_trade_orders:
            if i["status"] == "pending":
                open_orders.append(i)
        return open_orders

    def get_order(self, symbol, order_id) -> dict:
        for i in self.paper_trade_orders:
            if i["id"] == order_id:
                return i

    def get_products(self):
        def get_keyless_products():
            symbols_ = []
            for full_symbol in self.full_prices:
                symbols_.append({
                    'symbol': full_symbol
                })
            self.get_products_cache = symbols_
        if self.backtesting:
            if self.get_products_cache is None:
                if self.get_exchange_type() == 'keyless':
                    get_keyless_products()
                else:
                    self.get_products_cache = self.calls.get_products()
            return self.get_products_cache
        else:
            if self.get_exchange_type() == 'keyless':
                get_keyless_products()
                return self.get_products_cache
            else:
                return self.calls.get_products()

    def get_fees(self, symbol):
        if self.backtesting:
            # Add exchanges that actually require a symbol
            type_ = self.get_exchange_type()
            if type_ == 'okx' or type_ == 'binance':
                if symbol not in self.get_fees_cache:
                    self.get_fees_cache[symbol] = self.calls.get_fees(symbol)
                    return self.get_fees_cache[symbol]
                else:
                    return self.get_fees_cache[symbol]
            # If it doesn't require a symbol just store it in the root
            else:
                if self.get_fees_cache == {}:
                    self.get_fees_cache = self.calls.get_fees(symbol)
                    return self.get_fees_cache
                else:
                    return self.get_fees_cache
        else:
            return self.calls.get_fees(symbol)

    def get_product_history(self, symbol, epoch_start, epoch_stop, resolution):
        if self.backtesting:
            return utils.extract_price_by_resolution(self.full_prices, symbol, epoch_start, epoch_stop, resolution)
        else:
            return self.calls.get_product_history(symbol, epoch_start, epoch_stop, resolution)

    def get_order_filter(self, symbol):
        # Don't re-query order filter if its cached
        if symbol not in self.get_order_filter_cache:
            self.get_order_filter_cache[symbol] = self.calls.get_order_filter(symbol)

        if self.get_exchange_type() == 'binance':
            self.get_order_filter_cache[symbol] = self.__evaluate_binance_limits(self.get_price(symbol),
                                                                                 self.get_order_filter_cache[symbol])
        return self.get_order_filter_cache[symbol]

    def get_price(self, symbol) -> float:
        if self.backtesting:
            return self.get_backtesting_price(symbol)
        else:
            return self.calls.get_price(symbol)

    @staticmethod
    def __evaluate_binance_limits(price: (int, float), order_filter):
        order_filter['limit_order']['min_price'] = order_filter['exchange_specific']['limit_multiplier_down'] * price
        order_filter['limit_order']['max_price'] = order_filter['exchange_specific']['limit_multiplier_up'] * price
        return order_filter
