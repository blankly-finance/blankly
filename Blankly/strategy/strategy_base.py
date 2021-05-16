import Blankly

class Strategy(Blankly.Bot):
    def main(self, args):
        self.ticker = self.Ticker_manager.get_ticker()
        self.orderbook = self.Orderbook_manager.get_ticker()

    def add_price_event(self, callback, resolution):
        """
        Add Orderbook Event
        Args:
            callback: The price event callback that will be added to the current ticker and run at the proper resolution
            resolution: The resolution that the callback will be run
        """
        self.ticker.append_callback(Blankly.Scheduler(callback, resolution))

    def add_orderbook_event(self, callback):
        """
        Add Orderbook Event
        Args:
            callback: The Orderbook callback that will be added to the current ticker orderbook
        """
        self.orderbook.append_callback(callback)