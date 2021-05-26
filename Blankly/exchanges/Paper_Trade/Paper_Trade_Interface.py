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


from Blankly.interface.currency_Interface import CurrencyInterface
from Blankly.exchanges.Paper_Trade.backtesting_wrapper import BacktestingWrapper


from Blankly.utils.exceptions import InvalidOrder
from Blankly.utils.exceptions import APIException

import Blankly.utils.paper_trading.local_account.trade_local as trade_local
import Blankly.utils.paper_trading.utils as paper_trade
import Blankly.utils.utils as utils


from Blankly.utils.purchases.limit_order import LimitOrder
from Blankly.utils.purchases.market_order import MarketOrder

import warnings
import time
import threading
import traceback


class PaperTradeInterface(CurrencyInterface, BacktestingWrapper):
    def __init__(self, derived_interface):
        self.paper_trade_orders = []

        CurrencyInterface.__init__(self, "paper_trade", derived_interface)
        BacktestingWrapper.__init__(self)

        # Write in the accounts to our local account. This involves getting the values directly from the exchange
        accounts = self.calls.get_account()
        value_pairs = {}

        # Iterate & pair
        for i in accounts:
            value_pairs[i['currency']] = i['available']

        self.get_products_cache = None
        self.get_fees_cache = None
        self.get_market_limits_cache = None

        self.__exchange_properties = None

        self.__run_watchdog = True

        # Initialize the local account
        trade_local.init_local_account(value_pairs)

    def init_exchange(self):
        try:
            fees = self.calls.get_fees()
        except AttributeError:
            traceback.print_exc()
            raise AttributeError("Are you passing a non-interface object into the paper trade constructor?")

        self.__exchange_properties = {
            "maker_fee_rate": fees['maker_fee_rate'],
            "taker_fee_rate": fees['taker_fee_rate']
        }

    """ Needs to be overridden here """
    def start_paper_trade_watchdog(self):
        # TODO, this process could use variable update time/websocket usage, poll time and a variety of settings
        #  to create a robust trading system
        # Create the watchdog for watching limit orders
        self.__thread = threading.Thread(target=self.__paper_trade_watchdog())
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

    def evaluate_limits(self):
        """
        When this is run it checks the local paper trade orders to see if any need to go through
        """
        used_currencies = []
        for i in self.paper_trade_orders:
            if i["product_id"] not in used_currencies:
                used_currencies.append(i['product_id'])
        prices = {}

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
            if index['type'] == 'limit' and index['status'] == 'pending':
                current_price = prices[index['product_id']]

                if index['side'] == 'buy':
                    if index['price'] > current_price:
                        order, funds = self.evaluate_paper_trade(index, current_price)
                        trade_local.trade_local(currency_pair=index['product_id'],
                                                side='buy',
                                                base_delta=float(order['filled_size']),  # Gain filled size after fees
                                                quote_delta=funds * -1)  # Loose the original fund amount
                        order['status'] = 'done'
                        order['settled'] = 'true'

                        self.paper_trade_orders[i] = order
                elif index['side'] == 'sell':
                    if index['price'] < prices[index['product_id']]:
                        order, funds = self.evaluate_paper_trade(index, current_price)
                        trade_local.trade_local(currency_pair=index['product_id'],
                                                side='sell',
                                                base_delta=float(index['size'] * - 1),  # Loose size before any fees
                                                quote_delta=index['executed_value'])  # Gain executed value after fees
                        order['status'] = 'done'
                        order['settled'] = 'true'

                        self.paper_trade_orders[i] = order

    def evaluate_paper_trade(self, order, current_price):
        """
        This calculates fees & evaluates accurate value
        Args:
            order (dict): Order dictionary to derive the order attributes
            current_price (float): The current price of the currency pair the limit order was created on
        """
        funds = order['size'] * current_price
        executed_value = funds - funds * float((self.exchange_properties["maker_fee_rate"]))
        fill_fees = funds * float((self.exchange_properties["maker_fee_rate"]))
        fill_size = order['size'] - order['size'] * float((self.exchange_properties["maker_fee_rate"]))

        order['executed_value'] = str(executed_value)
        order['fill_fees'] = str(fill_fees)
        order['filled_size'] = str(fill_size)

        return order, funds

    def get_account(self, currency=None):
        needed = self.needed['get_account']

        # TODO this can be optimized
        local_account = trade_local.get_accounts()
        accounts = []
        for key, value in local_account.items():
            accounts.append({
                'currency': key,
                'balance': value,
                'available': value,
                'hold': 0
            })

        # We have to sort through it if the accounts are none
        if currency is not None:
            for i in accounts:
                if i["currency"] == currency:
                    parsed_value = utils.isolate_specific(needed, i)
                    return parsed_value
            warnings.warn("Currency not found")
        for i in range(len(accounts)):
            accounts[i] = utils.isolate_specific(needed, accounts[i])
        return accounts

    def market_order(self, product_id, side, funds) -> MarketOrder:
        print("Paper Trading...")
        needed = self.needed['market_order']
        order = {
            'funds': funds,
            'side': side,
            'product_id': product_id,
            'type': 'market'
        }
        creation_time = self.time()
        price = self.get_price(product_id)

        market_limits = self.get_market_limits(product_id)
        if "min_market_funds" in market_limits['exchange_specific']:
            min_funds = float(market_limits["exchange_specific"]["min_market_funds"])
        else:
            min_funds = float(market_limits["base_min_size"]) * price

        if funds < min_funds:
            raise InvalidOrder("Invalid Order: funds is too small. Minimum is: " + str(min_funds))

        qty = funds / price

        if not trade_local.test_trade(product_id, side, qty , price):
            raise InvalidOrder("Invalid Order: Insufficient funds")
        # Create coinbase pro-like id
        coinbase_pro_id = paper_trade.generate_coinbase_pro_id()
        # TODO the force typing here isn't strictly necessary because its run int the isolate_specific anyway
        response = {
            'id': str(coinbase_pro_id),
            'side': str(side),
            'type': 'market',
            'status': 'done',
            'product_id': str(product_id),
            'funds': str(funds - funds * float((self.__exchange_properties["maker_fee_rate"]))),
            'specified_funds': str(funds),
            'post_only': 'false',
            'created_at': str(creation_time),
            'done_at': str(self.time()),
            'done_reason': 'filled',
            'fill_fees': str(funds * float((self.__exchange_properties["maker_fee_rate"]))),
            'filled_size': str(funds - funds * float((self.__exchange_properties["maker_fee_rate"])) / price),
            'executed_value': str(funds - funds * float((self.__exchange_properties["maker_fee_rate"]))),
            'settled': 'true'
        }
        response = utils.isolate_specific(needed, response)
        self.paper_trade_orders.append(response)
        if side == "buy":
            trade_local.trade_local(currency_pair=product_id,
                                    side=side,
                                    base_delta=qty - qty * float((self.__exchange_properties["maker_fee_rate"])),
                                    # Gain filled size after fees
                                    quote_delta=funds * -1  # Loose the original fund amount
                                    )
        elif side == "sell":
            trade_local.trade_local(currency_pair=product_id,
                                    side=side,
                                    base_delta=float(qty - 1),  # Loose size before any fees
                                    quote_delta=funds - funds * float((self.__exchange_properties["maker_fee_rate"]))
                                    # Gain executed value after fees
                                    )
        else:
            raise APIException("Invalid trade side: " + str(side))
        return MarketOrder(order, response, self)

    def limit_order(self, product_id, side, price, size) -> LimitOrder:
        """
        Used for buying or selling limit orders
        Args:
            product_id: currency to buy
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
            'product_id': product_id,
            'type': 'limit'
        }
        creation_time = self.time()
        min_base = float(self.get_market_limits(product_id)["base_min_size"])
        if size < min_base:
            raise InvalidOrder("Invalid Order: Order quantity is too small. Minimum is: " + str(min_base))

        if not trade_local.test_trade(product_id, side, size, price):
            raise InvalidOrder("Invalid Order: Insufficient funds")

        # Create coinbase pro-like id
        coinbase_pro_id = paper_trade.generate_coinbase_pro_id()
        response = {
            'id': str(coinbase_pro_id),
            'price': str(price),
            'size': str(size),
            'product_id': str(product_id),
            'side': str(side),
            'stp': 'dc',
            'type': 'limit',
            "time_in_force": "GTC",
            'post_only': 'false',
            'created_at': str(creation_time),
            "fill_fees": "0.0000000000000000",
            "filled_size": "0.00000000",
            "executed_value": "0.0000000000000000",
            'status': 'pending',
            'settled': 'false'
        }
        response = utils.isolate_specific(needed, response)
        self.paper_trade_orders.append(response)
        return LimitOrder(order, response, self)

    def cancel_order(self, currency_id, order_id) -> dict:
        """
        This block could potentially work for both exchanges
        """
        order_index = None
        for i in range(len(self.paper_trade_orders)):
            index = self.paper_trade_orders[i]
            if index['status'] == 'pending' and index['id'] == order_id:
                order_index = i

        if order_index is not None:
            id = self.paper_trade_orders[order_index]['id']
            del self.paper_trade_orders[order_index]
            return {"order_id": id}

    def get_open_orders(self, product_id=None):
        open_orders = []
        for i in self.paper_trade_orders:
            if i["status"] == "open":
                open_orders.append(i)
        return open_orders

    def get_order(self, currency_id, order_id) -> dict:
        for i in self.paper_trade_orders:
            if i["id"] == order_id:
                return i

    def get_products(self):
        if self.backtesting:
            if self.get_products_cache is None:
                self.get_products_cache = self.calls.get_products()
            return self.get_products_cache
        else:
            return self.calls.get_products()

    def get_fees(self):
        if self.backtesting:
            if self.get_fees_cache is None:
                self.get_fees_cache = self.calls.get_fees()
            return self.get_fees_cache
        else:
            return self.calls.get_fees()

    def get_product_history(self, product_id, epoch_start, epoch_stop, granularity):
        if self.backtesting:
            raise APIException("Cannot download product history during a backtest")
        else:
            return self.calls.get_product_history(product_id, epoch_start, epoch_stop, granularity)

    def get_market_limits(self, product_id):
        if self.backtesting:
            if self.get_market_limits_cache is None:
                self.get_market_limits_cache = self.calls.get_market_limits(product_id)
            return self.get_market_limits_cache
        else:
            return self.calls.get_market_limits(product_id)

    def get_price(self, currency_pair) -> float:
        if self.backtesting:
            return self.get_backtesting_price(currency_pair)
        else:
            return self.calls.get_price(currency_pair)
