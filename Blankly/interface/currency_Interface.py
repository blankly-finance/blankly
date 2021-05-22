"""
    Logic to provide consistency across exchanges
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
import warnings
import threading
import Blankly.utils.utils as utils
import Blankly.utils.paper_trading.local_account.trade_local as trade_local
from Blankly.interface.abc_currency_interface import ICurrencyInterface
import abc


class CurrencyInterface(ICurrencyInterface, abc.ABC):
    def __init__(self, exchange_name, authenticated_API):
        self.exchange_name = exchange_name
        self.calls = authenticated_API
        # Reload user preferences here
        self.user_preferences = utils.load_user_preferences()
        self.paper_trading = self.user_preferences["settings"]["paper_trade"]
        self.paper_trade_orders = []
        # TODO, improve creation of its own properties
        self.exchange_properties = None
        # Some exchanges like binance will not return a value of 0.00 if there is no balance
        self.available_currencies = {}
        self.init_exchange()

        self.needed = {
            '__init_exchange__': [
                ['maker_fee_rate', float],
                ['taker_fee_rate', float]
            ],
            'get_products': [
                ["currency_id", str],
                ["base_currency", str],
                ["quote_currency", str],
                ["base_min_size", float],
                ["base_max_size", float],
                ["base_increment", float]
            ],
            'get_account': [
                ["currency", str],
                ["available", float],
                ["hold", float]
            ],
            'market_order': [
                ["product_id", str],
                ["id", str],
                ["created_at", float],
                ["funds", float],
                ["status", str],
                ["type", str],
                ["side", str]
            ],
            'limit_order': [
                ["product_id", str],
                ["id", str],
                ["created_at", float],
                ["price", float],
                ["size", float],
                ["status", str],
                ["time_in_force", str],
                ["type", str],
                ["side", str]
            ],
            'cancel_order': [
                ['order_id', str]
            ],
            'get_open_orders': [
                ["id", str],
                ["price", float],
                ["size", float],
                ["type", str],
                ["side", str],
                ["status", str]
            ],
            'get_order': [
                ["id", str],
                ["product_id", str],
                ["price", float],
                ["size", float],
                ["type", str],
                ["side", str],
                ["status", str],
                ["funds", float]
            ],
            'get_fees': [
                ['maker_fee_rate', float],
                ['taker_fee_rate', float]
            ],
            'get_market_limits': [
                ["market", str],
                ["base_currency", str],
                ["quote_currency", str],
                ["base_min_size", float],  # Minimum size to buy
                ["base_max_size", float],  # Maximum size to buy
                ["quote_increment", float],  # Specifies the min order price as well as the price increment.
                ["base_increment", float],  # Specifies the minimum increment for the base_currency.
                ["max_orders", int],
                ["min_price", float],
                ["max_price", float]
            ]
        }

        if self.paper_trading:
            # Write in the accounts to our local account. This involves getting the values directly from the exchange
            accounts = self.get_account(override_paper_trading=True)
            value_pairs = {}

            # Iterate & pair
            for i in accounts:
                value_pairs[i['currency']] = i['available']

            # Initialize the local account
            trade_local.init_local_account(value_pairs)

    @abc.abstractmethod
    def init_exchange(self):
        """
        Create the properties for the exchange.
        """
        pass

    """ Needs to be overridden here """
    def start_paper_trade_watchdog(self):
        if self.paper_trading:
            # TODO, this process could use variable update time/websocket usage, poll time and a variety of settings
            #  to create a robust trading system
            # Create the watchdog for watching limit orders
            self.__thread = threading.Thread(target=self.__paper_trade_watchdog())
            self.__thread.start()
        else:
            warnings.warn("Paper trading is not enabled - skipping start")

    """ Needs to be overridden here """
    def __paper_trade_watchdog(self):
        """
        Internal order watching system
        """
        time.sleep(10)
        used_currencies = []
        for i in self.paper_trade_orders:
            if i["product_id"] not in used_currencies:
                used_currencies.append(i['product_id'])
        prices = {}

        for i in used_currencies:
            prices[i] = self.get_price(i)
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

    """ Needs to be overridden here """
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

    """ Needs to be overridden here """
    def override_paper_trading(self, value):
        self.paper_trading = bool(value)

    def get_paper_trading_status(self):
        return self.paper_trading

    """ Needs to be overridden here """
    def get_calls(self):
        """
        Returns:
             The exchange's direct calls object. A Blankly Bot class should have immediate access to this by
             default
        """
        return self.calls

    """ Needs to be overridden here """
    def get_exchange_type(self):
        return self.exchange_name

    def get_account(self, currency=None, override_paper_trading=False):
        """
        Get all currencies in an account, or sort by currency/account_id
        Args:
            currency (Optional): Filter by particular currency
            override_paper_trading (Optional bool): If paper trading is enabled, setting this to true will get the
             actual account values

        Coinbase Pro: get_account
        Binance: get_account["balances"]
        """
        # Use an internal value because we don't want to modify the class's value - which could create issues
        internal_paper_trade = self.paper_trading
        if override_paper_trading:
            internal_paper_trade = False

        if currency is not None:
            currency = utils.get_base_currency(currency)

        return currency, internal_paper_trade

    def get_product_history(self, product_id, epoch_start, epoch_stop, granularity):
        return utils.convert_epochs(epoch_start), utils.convert_epochs(epoch_stop)

    """ 
    ATM it doesn't seem like the Binance library supports stop orders. 
    We need to add this when we implement our own.
    
    Leave the code here in this interface class because it may be used in any given inherited class
    """
    # def stop_order(self, product_id, side, price, size, **kwargs):
    #     """
    #     Used for placing stop orders
    #     Args:
    #         product_id: currency to buy
    #         side: buy/sell
    #         price: price to set limit order
    #         size: amount of currency (like BTC) for the limit to be valued
    #         kwargs: specific arguments that may be used by each exchange, (if exchange is known)
    #     """
    #     if self.__exchange_name == "coinbase_pro":
    #         """
    #         {
    #             "id": "d0c5340b-6d6c-49d9-b567-48c4bfca13d2",
    #             "price": "0.10000000",
    #             "size": "0.01000000",
    #             "product_id": "BTC-USD",
    #             "side": "buy",
    #             "stp": "dc",
    #             "type": "limit",
    #             "time_in_force": "GTC",
    #             "post_only": false,
    #             "created_at": "2016-12-08T20:02:28.53864Z",
    #             "fill_fees": "0.0000000000000000",
    #             "filled_size": "0.00000000",
    #             "executed_value": "0.0000000000000000",
    #             "status": "pending",
    #             "settled": false
    #         }
    #         """
    #         order = {
    #             'size': size,
    #             'side': side,
    #             'product_id': product_id,
    #             'type': 'stop'
    #         }
    #         self.__calls.placeOrder(product_id, side, price, size)
    #         response = self.__calls.place_market_order(product_id, side, price, size, kwargs=kwargs)
    #         return Purchase(order,
    #                         response,
    #                         self.__ticker_manager.get_ticker(product_id,
    #                                                          override_default_exchange_name="coinbase_pro"),
    #                         self.__exchange_properties)
    """
    Coinbase Pro: get_account_history
    Binance: 
        get_deposit_history
        get_withdraw_history
        
    """
