import time
from datetime import datetime
from operator import itemgetter

import pytest

from blankly.enums import Side, OrderType, ContractType, OrderStatus, HedgeMode, MarginType
from blankly.exchanges.interfaces.futures_exchange_interface import FuturesExchangeInterface
from blankly.utils import utils
from conftest import wait_till_filled, order_guard, homogenity_testing

def test_valid_symbols(futures_interface: FuturesExchangeInterface):
    # collect product names
    products = []
    products.extend(futures_interface.get_products().values())
    # TODO place order here
    # TODO contextmanager for order/cancel
    products.extend(futures_interface.get_positions().values())
    for product in products:
        base = product['base_asset']
        quote = product['quote_asset']
        symbol = product['symbol']
        assert symbol == base + '-' + quote
        exc = futures_interface.to_exchange_symbol(symbol)
        assert futures_interface.to_blankly_symbol(exc) == symbol




@homogenity_testing
def test_get_products(futures_interface: FuturesExchangeInterface):
    return list(futures_interface.get_products().values())


@homogenity_testing
def test_get_products_symbol(futures_interface: FuturesExchangeInterface,
                             symbol: str):
    return futures_interface.get_products(symbol)


@homogenity_testing
def test_get_account(futures_interface: FuturesExchangeInterface):
    return list(futures_interface.get_account().values())


@homogenity_testing
def test_get_positions(futures_interface: FuturesExchangeInterface):
    return list(futures_interface.get_positions().values())

@homogenity_testing
def test_get_positions_symbol(futures_interface: FuturesExchangeInterface,
                             symbol: str):
    return futures_interface.get_positions(symbol)


@order_guard
def test_order(futures_interface: FuturesExchangeInterface,
               symbol: str) -> None:
    init_position = futures_interface.get_positions(symbol).size
    product = futures_interface.get_products(symbol)
    price = futures_interface.get_price(symbol)
    size = utils.trunc(0.1 / price, product.price_precision)

    sell_order = futures_interface.market_order(symbol, Side.SELL, size)
    res = wait_till_filled(futures_interface, sell_order)

    assert res.side == Side.SELL
    assert res.type == OrderType.MARKET
    assert futures_interface.get_positions(symbol).size == init_position - size

    buy_order = futures_interface.market_order(symbol,
                                               Side.BUY,
                                               size,
                                               reduce_only=True)
    res = wait_till_filled(futures_interface, buy_order)

    assert res.side == Side.BUY
    assert res.type == OrderType.MARKET
    assert futures_interface.get_positions(symbol).size == init_position


@homogenity_testing
def test_market_order(futures_interface: FuturesExchangeInterface, symbol: str):
    pass  # TODO

@homogenity_testing
def test_limit_order(futures_interface: FuturesExchangeInterface, symbol: str):
    pass  # TODO

@homogenity_testing
def test_take_profit(futures_interface: FuturesExchangeInterface, symbol: str):
    pass  # TODO

@homogenity_testing
def test_stop_loss(futures_interface: FuturesExchangeInterface, symbol: str):
    pass  # TODO

def test_set_hedge_mode(futures_interface: FuturesExchangeInterface):
    if futures_interface.get_exchange_type() == 'ftx_futures':
        pytest.xfail('FTX Futures does not support hedge mode')
    futures_interface.set_hedge_mode(HedgeMode.HEDGE)
    assert futures_interface.get_hedge_mode() == HedgeMode.HEDGE

def test_set_oneway_mode(futures_interface: FuturesExchangeInterface):
    futures_interface.set_hedge_mode(HedgeMode.ONEWAY)
    assert futures_interface.get_hedge_mode() == HedgeMode.ONEWAY

def test_account_leverage(futures_interface: FuturesExchangeInterface):
    if futures_interface.get_exchange_type() == 'binance_futures':
        pytest.xfail(
            'Binance Futures does not support setting account leverage')
    futures_interface.set_leverage(3)
    assert futures_interface.get_leverage() == 3


def test_symbol_leverage(futures_interface: FuturesExchangeInterface,
                         symbol: str):
    if futures_interface.get_exchange_type() == 'ftx_futures':
        pytest.xfail('FTX Futures does not support setting account leverage')
    futures_interface.set_leverage(3, symbol)
    assert futures_interface.get_leverage(symbol) == 3


def test_set_cross_margin(futures_interface: FuturesExchangeInterface, symbol: str):
    futures_interface.set_margin_type(symbol, MarginType.CROSSED)
    assert futures_interface.get_margin_type(symbol) == MarginType.CROSSED

def test_set_isolated_margin(futures_interface: FuturesExchangeInterface, symbol: str):
    if futures_interface.get_exchange_type() == 'ftx_futures':
        pytest.xfail('FTX Futures does not support isolated margin')
    futures_interface.set_margin_type(symbol, MarginType.ISOLATED)
    assert futures_interface.get_margin_type(symbol) == MarginType.ISOLATED

@order_guard
def test_cancel_order(futures_interface: FuturesExchangeInterface,
                      symbol: str):
    init_position = futures_interface.get_positions(symbol).size
    product = futures_interface.get_products(symbol)

    price = futures_interface.get_price(symbol)
    size = utils.trunc(0.1 / price, product.size_precision)
    buy_order = futures_interface.limit_order(
        symbol, Side.BUY, utils.trunc(price * 0.95, product.price_precision),
        size)

    assert buy_order.status == OrderStatus.OPEN

    res = futures_interface.cancel_order(symbol, buy_order.id)
    assert res.status == OrderStatus.CANCELED
    assert init_position == futures_interface.get_positions(symbol).size

@homogenity_testing
def test_get_open_orders(futures_interface: FuturesExchangeInterface, symbol: str):
    pass  # TODO

@homogenity_testing
def test_get_order(futures_interface: FuturesExchangeInterface, symbol: str):
    pass  # TODO

@homogenity_testing
def test_price(futures_interface: FuturesExchangeInterface, symbol: str):
    price = futures_interface.get_price(symbol)
    assert 0 < price
    return price

@homogenity_testing
def test_funding_rate_history(futures_interface: FuturesExchangeInterface,
                              symbol: str):
    day = 60 * 60 * 24
    now = int(datetime.now().timestamp())
    start = now - day * 365
    end = now - day * 7
    history = futures_interface.get_funding_rate_history(symbol=symbol,
                                                         epoch_start=start,
                                                         epoch_stop=end)

    # non-perp contracts don't have funding rates
    if futures_interface.get_products(
    )[symbol].contract_type != ContractType.PERPETUAL:
        assert len(history) == 0
        return

    # test start and end times
    assert start <= history[0]['time'] < start + day
    assert end - day < history[-1]['time'] <= end

    # test ascending order
    assert sorted(history, key=itemgetter('time')) == history

    # test resolution
    resolution = futures_interface.get_funding_rate_resolution()
    for i, current in enumerate(history)[1:]:
        prev = history[i-1]
        assert current['time'] - prev['time'] == resolution

    return history