from Blankly.strategy.order import Order
import Blankly
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
            self.Ticker_Manager.append_callback(callback)
            # Blankly.Scheduler(self.price_event_websocket, resolution, callback=callback)
        else:
            Blankly.Scheduler(self.price_event_rest, resolution, callback=callback)

    def add_orderbook_event(self, callback, resolution):
        """
        Add Orderbook Event
        Args:
            callback: The price event callback that will be added to the current ticker and run at the proper resolution
            resolution: The resolution that the callback will be run
        """
        self.Orderbook_Manager.append_callback(callback)

    def price_event_rest(self, callback):
        price = self.Interface.get_price(self.currency_pair)
        callback(price, self.currency_pair)
        return

    def price_event_websocket(self, callback):
        price = self.Ticker_Manager.get_most_recent_tick()
        callback(price, self.currency_pair)
        return
