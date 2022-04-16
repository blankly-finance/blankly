import sys
import time
from datetime import datetime
from operator import itemgetter

import pytest
from _pytest.python_api import approx

from blankly.enums import Side, OrderType, ContractType, OrderStatus, HedgeMode, MarginType, PositionMode, TimeInForce
from blankly.exchanges.interfaces.futures_exchange_interface import FuturesExchangeInterface
from blankly.utils import utils
from tests.new_interface_tests.test_utils import wait_till_filled, homogeneity_testing, sell, buy, cancelling_order, close_position, \
    close_all

# TODO auto truncate
# TODO min size/min notional api


def valid_product_helper(futures_interface: FuturesExchangeInterface, product):
    base = product['base_asset']
    quote = product['quote_asset']
    symbol = product['symbol']
    assert symbol == base + '-' + quote
    exc = futures_interface.to_exchange_symbol(symbol)
    assert futures_interface.to_blankly_symbol(exc) == symbol


def test_valid_symbols(futures_interface: FuturesExchangeInterface):
    for product in futures_interface.get_products().values():
        valid_product_helper(futures_interface, product)


def test_valid_symbol_from_position(
        futures_interface: FuturesExchangeInterface, symbol: str):
    with cancelling_order(futures_interface, symbol):
        products = futures_interface.get_positions().values()
    for product in products:
        valid_product_helper(futures_interface, product)


@homogeneity_testing
def test_get_products(futures_interface: FuturesExchangeInterface):
    return list(futures_interface.get_products().values())


@homogeneity_testing
def test_get_products_symbol(futures_interface: FuturesExchangeInterface,
                             symbol: str):
    return futures_interface.get_products(symbol)


@homogeneity_testing
def test_get_account(futures_interface: FuturesExchangeInterface):
    return list(futures_interface.get_account().values())


@homogeneity_testing
def test_get_positions(futures_interface: FuturesExchangeInterface):
    return list(futures_interface.get_positions().values())


@homogeneity_testing
@pytest.mark.parametrize('side', [Side.BUY, Side.SELL])
def test_get_positions(futures_interface: FuturesExchangeInterface,
                       symbol: str, side: Side):
    if side == Side.BUY:
        func = buy
        m = 1
    elif side == Side.SELL:
        func = sell
        m = -1

    close_position(futures_interface, symbol)

    order = func(futures_interface, symbol)
    position = futures_interface.get_positions(symbol)
    assert position.symbol == symbol
    assert m * position.size == order.size
    assert 0 < position.size * m
    assert position.leverage == futures_interface.get_leverage(symbol)
    # assert position.margin_type == futures_interface.get_margin_type(symbol)

    close_position(futures_interface, symbol)

    return position


def test_simple_open_close(futures_interface: FuturesExchangeInterface,
                           symbol: str) -> None:
    close_position(futures_interface, symbol)

    # buy
    size = buy(futures_interface, symbol).size
    assert futures_interface.get_positions(symbol).size == approx(size)

    close_position(futures_interface, symbol)

    # sell
    size = sell(futures_interface, symbol).size
    assert futures_interface.get_positions(symbol).size == approx(-size)

    close_position(futures_interface, symbol)


@homogeneity_testing
@pytest.mark.parametrize('side', [Side.BUY, Side.SELL])
def test_order(futures_interface: FuturesExchangeInterface, symbol: str,
               side: Side):
    close_position(futures_interface, symbol)

    price = futures_interface.get_price(symbol)
    product = futures_interface.get_products(symbol)
    size = utils.trunc(13 / price, product.size_precision)
    order = futures_interface.market_order(symbol, side, size)

    assert order.symbol == symbol
    assert 0 <= order.id
    assert order.size == approx(size, rel=0.01)
    assert order.status in (OrderStatus.OPEN, OrderStatus.FILLED)
    assert order.type == OrderType.MARKET
    assert order.contract_type == ContractType.PERPETUAL
    assert order.side == side
    assert order.limit_price == 0
    assert order.position == PositionMode.BOTH
    assert order.time_in_force == TimeInForce.GTC

    res = wait_till_filled(futures_interface,
                           order)  # for market orders, just wait for fil

    # make sure we paid what we expect
    assert res.price == approx(size * price, rel=0.01)

    # check our stake is increased/decreased
    position_size = futures_interface.get_positions(symbol).size
    if side == Side.BUY:
        assert order.size == position_size
    else:
        assert order.size == -position_size

    # close position
    close_position(futures_interface, symbol)

    # set price, status and make sure order/res are otherwise equal
    order.price = res.price
    order.status = res.status
    assert order == res

    return order


@homogeneity_testing
@pytest.mark.parametrize(
    'type', [OrderType.LIMIT, OrderType.TAKE_PROFIT, OrderType.STOP])
@pytest.mark.parametrize('side', [Side.BUY, Side.SELL])
def test_priced_orders(futures_interface: FuturesExchangeInterface,
                       symbol: str, side: Side, type: OrderType):
    close_position(futures_interface, symbol)

    price = futures_interface.get_price(symbol)
    product = futures_interface.get_products(symbol)
    size = utils.trunc(20 / price, product.size_precision)
    m = 0.3
    if side == Side.BUY:
        m = -m
    if type == OrderType.STOP:
        m = -m
    limit_price = utils.trunc(price * (1 + m), product.price_precision)
    if type == OrderType.LIMIT:
        order = futures_interface.limit_order(symbol, side, limit_price, size)
    elif type == OrderType.TAKE_PROFIT:
        order = futures_interface.take_profit(symbol, side, limit_price, size)
    elif type == OrderType.STOP:
        order = futures_interface.stop_loss(symbol, side, limit_price, size)

    assert order.symbol == symbol
    assert 0 <= order.id
    assert order.size == approx(size, rel=0.01)
    assert order.status == OrderStatus.OPEN
    assert order.type == type
    assert order.contract_type == ContractType.PERPETUAL
    assert order.side == side
    assert order.limit_price == limit_price
    assert order.position == PositionMode.BOTH
    assert order.time_in_force == TimeInForce.GTC

    res = futures_interface.cancel_order(symbol, order.id)

    order.status = OrderStatus.CANCELED
    assert order == res

    return order


def test_set_hedge_mode(futures_interface: FuturesExchangeInterface):
    if futures_interface.get_exchange_type() == 'ftx_futures':
        pytest.xfail('FTX Futures does not support hedge mode')
    close_all(futures_interface)
    futures_interface.set_hedge_mode(HedgeMode.HEDGE)
    assert futures_interface.get_hedge_mode() == HedgeMode.HEDGE


def test_set_oneway_mode(futures_interface: FuturesExchangeInterface):
    close_all(futures_interface)
    futures_interface.set_hedge_mode(HedgeMode.ONEWAY)
    assert futures_interface.get_hedge_mode() == HedgeMode.ONEWAY


def test_account_leverage(futures_interface: FuturesExchangeInterface):
    close_all(futures_interface)
    if futures_interface.get_exchange_type() == 'binance_futures':
        pytest.xfail(
            'Binance Futures does not support setting account leverage')
    futures_interface.set_leverage(3)
    assert futures_interface.get_leverage() == 3


def test_symbol_leverage(futures_interface: FuturesExchangeInterface,
                         symbol: str):
    if futures_interface.get_exchange_type() == 'ftx_futures':
        close_all(futures_interface)
        futures_interface.set_leverage(3)  # set globally for ftx
        with pytest.raises(
                Exception):  # changing for symbol should raise an exception
            futures_interface.set_leverage(3, symbol)
    else:
        # for other exchanges we can proceed as normal
        close_position(futures_interface, symbol)
        futures_interface.set_leverage(3, symbol)
    assert futures_interface.get_leverage(symbol) == 3


def test_set_cross_margin(futures_interface: FuturesExchangeInterface,
                          symbol: str):
    if futures_interface.get_exchange_type() == 'binance_futures':
        pytest.xfail('Binance doesn\'t have an API for this')
    close_all(futures_interface)
    futures_interface.set_margin_type(symbol, MarginType.CROSSED)
    assert futures_interface.get_margin_type(symbol) == MarginType.CROSSED


def test_set_isolated_margin(futures_interface: FuturesExchangeInterface,
                             symbol: str):
    if futures_interface.get_exchange_type() == 'ftx_futures':
        pytest.xfail('FTX Futures does not support isolated margin')
    futures_interface.set_margin_type(symbol, MarginType.ISOLATED)

    if futures_interface.get_exchange_type() == 'binance_futures':
        pytest.xfail('Binance doesn\'t have an API for this')
    assert futures_interface.get_margin_type(symbol) == MarginType.ISOLATED


@homogeneity_testing
def test_get_open_orders(futures_interface: FuturesExchangeInterface,
                         symbol: str):
    with cancelling_order(futures_interface, symbol) as order:
        open_orders = futures_interface.get_open_orders(symbol)
    assert order in open_orders
    assert all(o.symbol == symbol for o in open_orders)
    return open_orders


@homogeneity_testing
def test_get_order(futures_interface: FuturesExchangeInterface, symbol: str):
    with cancelling_order(futures_interface, symbol) as order:
        assert futures_interface.get_order(symbol, order.id) == order


@homogeneity_testing
def test_price(futures_interface: FuturesExchangeInterface, symbol: str):
    price = futures_interface.get_price(symbol)
    assert 0 < price
    return price


@homogeneity_testing
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
    errors = []
    resolution = futures_interface.get_funding_rate_resolution()
    for i in range(1, len(history)):
        prev = history[i - 1]
        current = history[i]
        real_res = current['time'] - prev['time']
        if real_res != resolution:
            errors.append(current)
            print(
                f'wrong resolution in funding rate data: {real_res}, should be {resolution}',
                file=sys.stderr)
            if len(errors) > 20:
                pytest.fail(f'too many incorrect resolutions: errors={errors}')
                # pytest.fail(f'too many incorrect resolutions: {errors=}')

    return history
