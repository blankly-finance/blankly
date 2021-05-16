import Blankly

class Strategy(Blankly.Bot):
    def __init__(self):
        """
        Initializes Strategy base
        """
        super.__init__()
        self.price_event_funcs = []
        self.orderbook_event_funcs = []
    def main(self, args):
        self.ticker = self.Ticker_manager.create_ticker(callback=self.price_event)
        self.orderbook = self.Orderbook_manager.create_ticker(callback=self.price_event)

    def add_price_event(self, func, resolution):
        self.ticker.append_callback(Blankly.Scheduler(func, resolution))

    def add_orderbook_event(self, func):
        self.orderbook.append_callback(func)