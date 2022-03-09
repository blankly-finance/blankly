import time
from operator import itemgetter

from blankly import BinanceFutures, Side, OrderStatus, OrderType
from blankly.exchanges.futures.futures_exchange import FuturesExchange
from blankly.exchanges.interfaces.ftx_futures.ftx_futures import FTXFutures
from blankly.exchanges.interfaces.futures_exchange_interface import FuturesExchangeInterface
from datetime import datetime


def pytest_generate_tests(metafunc):
    # called for each test function

    # for now, only parametrize first fixture
    # the rest can be used for other things
    fixture = metafunc.fixturenames[0]

    # get parameters from class variable with same name
    # is there a better way to do this? getattr is stinky
    values = getattr(metafunc.cls, fixture)

    # parametrize!
    metafunc.parametrize(fixture, values, ids=[v.get_type() for v in values])


class TestInterfaces:
    # yapf: disable
    futures_exchange = (
        BinanceFutures(keys_path="./tests/config/keys.json",
                       preferences_path="./tests/config/settings.json",
                       portfolio_name="Futures Test Key"),
        FTXFutures(keys_path="./tests/config/keys.json",
                   preferences_path="./tests/config/settings.json",
                   portfolio_name="Test Account"),
    )

    # yapf: enable

    def test_account(self, futures_exchange: FuturesExchange):
        interface = futures_exchange.interface

        res = interface.get_account()
        assert 0 <= res.USDT.available

    def test_order(self, futures_exchange: FuturesExchange) -> None:
        interface = futures_exchange.interface

        symbol = 'BTC-USDT'
        sell_order = interface.market_order(symbol, Side.SELL, .01)

        retries = 0
        res = interface.get_order(symbol, sell_order.id)
        while res.status != OrderStatus.FILLED:
            if retries > 2:
                raise TimeoutError(
                    f"order was not filled. status: {res.status}")
            time.sleep(1 << retries)
            retries += 1
            res = interface.get_order(symbol, sell_order.id)

        assert res.side == Side.SELL
        assert res.type == OrderType.MARKET

        buy_order = interface.market_order(symbol, Side.BUY, .01)

        retries = 0
        res = interface.get_order(symbol, buy_order.id)
        while res.status != OrderStatus.FILLED:
            if retries > 2:
                raise TimeoutError("order was not filled")
            time.sleep(1 << retries)
            retries += 1
            res = interface.get_order(buy_order.id)

        assert res.side == Side.BUY
        assert res.type == OrderType.MARKET

    def test_cancel_order(self, futures_exchange: FuturesExchange):
        interface = futures_exchange.interface

        symbol = 'BTC-USDT'
        price = int(interface.get_price(symbol) * 0.8)
        buy_order = interface.limit_order(symbol, Side.BUY, price, .01)

        assert buy_order.status == OrderStatus.NEW

        retries = 0
        res = interface.cancel_order(symbol, buy_order.id)
        while res.status != OrderStatus.CANCELED:
            if retries > 2:
                raise TimeoutError("order was not cancelled")
            time.sleep(1 << retries)
            retries += 1
            res = interface.get_order(symbol, buy_order.id)

    def test_funding_rate_history(self, futures_exchange: FuturesExchange):
        interface = futures_exchange.interface

        day = 60 * 60 * 24
        now = int(datetime.now().timestamp())
        start = now - day * 365
        end = now - day * 7
        history = interface.get_funding_rate_history(symbol='BTC-USDT',
                                                     epoch_start=start,
                                                     epoch_stop=end)

        # test start and end times
        assert start <= history[0]['time'] < start + day
        assert end - day < history[-1]['time'] <= end

        # test ascending order
        assert sorted(history, key=itemgetter('time')) == history
