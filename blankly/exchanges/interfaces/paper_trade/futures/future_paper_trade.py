from blankly.exchanges.futures.futures_exchange import FuturesExchange
from blankly.exchanges.interfaces.futures_exchange_interface import FuturesExchangeInterface
from blankly.exchanges.interfaces.paper_trade.futures.futures_paper_trade_interface import FuturesPaperTradeInterface


class FuturesPaperTrade(FuturesExchange):
    def __init__(self,
                 exchange,
                 portfolio_name: str = None,
                 preferences_path: str = None,
                 initial_account_values: dict = None):
        super().__init__("futures_paper_trade", portfolio_name, preferences_path)

        self.exchange = exchange
        self._interface = FuturesPaperTradeInterface(exchange, initial_account_values or {})

    @property
    def calls(self):
        return self.exchange.calls

    @property
    def interface(self) -> FuturesExchangeInterface:
        return self._interface
