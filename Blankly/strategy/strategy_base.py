import Blankly
from Blankly.strategy.order import Order
from Blankly.utils.time_builder import time_interval_to_seconds


class Strategy(Blankly.BlanklyBot):
    def __init__(self):
        self.price_funcs = []
        self.order_funcs = []
    def main(self, args):
        pass

    def add_price_event(self, callback, resolution):
        """
        Add Orderbook Event
        Args:
            callback: The price event callback that will be added to the current ticker and run at the proper resolution
            resolution: The resolution that the callback will be run
        """
        if time_interval_to_seconds(resolution) < 60:
            # since it's less than 60, we will just use the websocket feed
            self.Ticker_Manager.append_callback(self._price_event_websocket(callback))
        else:
            # use the API 
            Blankly.Scheduler(self._price_event_rest, resolution, callback=callback)

    def add_orderbook_event(self, callback):
        """
        Add Orderbook Event
        Args:
            callback: The price event callback that will be added to the current ticker and run at the proper resolution
            resolution: The resolution that the callback will be run
        """
        self.Orderbook_Manager.append_callback(self.orderbook_event(callback))

    def _price_event_rest(self, callback):
        price = self.Interface.get_price(self.currency_pair)
        order = callback(price, self.currency_pair)
        if order != None:
            if not isinstance(order, Order):
                raise TypeError("Expected an order type of Order when order is not none but got {}".format(type(order)))
            else:
                if order.type == 'limit':
                    return self.Interface.limit_order(self.currency_pair, order.side, order.price, order.size)
                return self.Interface.market_order(self.currency_pair, order.side, order.price, order.size)
        return

    def _price_event_websocket(self, callback):
        price = self.Ticker_Manager.get_most_recent_tick()
        callback(price, self.currency_pair)
        return

    def _orderbook_event(self, callback):
        orderbook = self.Ticker_Manager.get_most_recent_tick()
        order = callback(orderbook, self.currency_pair)
        if order != None:
            if not isinstance(order, Order):
                raise TypeError("Expected an order type of Order when order is not none but got {}".format(type(order)))
            else:
                if order.type == 'limit':
                    return self.Interface.limit_order(self.currency_pair, order.side, order.price, order.size)
                return self.Interface.market_order(self.currency_pair, order.side, order.price, order.size)
        return
