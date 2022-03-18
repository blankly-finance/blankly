import sys
import time
from datetime import datetime
from operator import itemgetter

import pytest
from _pytest.python_api import approx

from blankly.enums import Side, OrderType, ContractType, OrderStatus, HedgeMode, MarginType
from blankly.exchanges.interfaces.futures_exchange_interface import FuturesExchangeInterface
from blankly.utils import utils
from conftest import wait_till_filled, order_guard, homogenity_testing, sell, buy, cancelling_order, close_position, \
    close_all_position


# TODO auto truncate
# TODO min size/min notional api


def valid_product_helper(futures_interface: FuturesExchangeInterface, product):
    base = product['base_asset']
    quote = product['quote_asset']
    symbol = product['symbol']
    assert symbol == base + '-' + quote
    exc = futures_interface.to_exchange_symbol(symbol)
    print(f'{exc=} {futures_interface.to_blankly_symbol(exc)=} {symbol=}')
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
@pytest.mark.parametrize('side', [Side.BUY, Side.SELL], ids=['buy', 'sell'])
def test_get_positions(futures_interface: FuturesExchangeInterface, symbol: str, side: Side):
    if side == Side.BUY:
        func = buy
        m = 1
    elif side == Side.SELL:
        func = sell
        m = -1

    close_position(futures_interface, symbol)
    assert futures_interface.get_positions(symbol) is None

    order = func(futures_interface, symbol)
    position = futures_interface.get_positions(symbol)
    assert position.symbol == symbol
    assert m * position.size == order.size
    assert 0 < position.size * m
    assert position.leverage == futures_interface.get_leverage(symbol)
    # assert position.margin_type == futures_interface.get_margin_type(symbol)

    close_position(futures_interface, symbol)
    assert futures_interface.get_positions(symbol) == None

    return position


@order_guard
def test_sell_buy(futures_interface: FuturesExchangeInterface,
                  symbol: str) -> None:
    init_position = futures_interface.get_positions(symbol).size

    # short position
    size = sell(futures_interface, symbol).size
    assert futures_interface.get_positions(symbol).size == approx(
        init_position - size)

    # buy back
    buy(futures_interface, symbol)
    assert futures_interface.get_positions(symbol).size == approx(
        init_position)


@order_guard
def test_sell_buy(futures_interface: FuturesExchangeInterface,
                  symbol: str) -> None:
    init_position = futures_interface.get_positions(symbol).size

    # long position
    size = buy(futures_interface, symbol).size
    assert futures_interface.get_positions(symbol).size == approx(
        init_position + size)

    # now sell
    sell(futures_interface, symbol)
    assert futures_interface.get_positions(symbol).size == approx(
        init_position)


@homogenity_testing
def test_market_order(futures_interface: FuturesExchangeInterface,
                      symbol: str):
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


# def test_set_hedge_mode(futures_interface: FuturesExchangeInterface):
#     if futures_interface.get_exchange_type() == 'ftx_futures':
#         pytest.xfail('FTX Futures does not support hedge mode')
#     futures_interface.set_hedge_mode(HedgeMode.HEDGE)
#     assert futures_interface.get_hedge_mode() == HedgeMode.HEDGE
#
#
# def test_set_oneway_mode(futures_interface: FuturesExchangeInterface):
#     futures_interface.set_hedge_mode(HedgeMode.ONEWAY)
#     assert futures_interface.get_hedge_mode() == HedgeMode.ONEWAY


def test_account_leverage(futures_interface: FuturesExchangeInterface):
    close_all_position(futures_interface)
    if futures_interface.get_exchange_type() == 'binance_futures':
        pytest.xfail(
            'Binance Futures does not support setting account leverage')
    futures_interface.set_leverage(3)
    assert futures_interface.get_leverage() == 3



def test_symbol_leverage(futures_interface: FuturesExchangeInterface,
                         symbol: str):
    if futures_interface.get_exchange_type() == 'ftx_futures':
        close_all_position(futures_interface)
        futures_interface.set_leverage(3)  # set globally for ftx
        with pytest.raises(Exception):
            futures_interface.set_leverage(3, symbol)
    else:
        close_position(futures_interface, symbol)
        futures_interface.set_leverage(3, symbol)
    assert futures_interface.get_leverage(symbol) == 3


# def test_set_cross_margin(futures_interface: FuturesExchangeInterface,
#                           symbol: str):
#     futures_interface.set_margin_type(symbol, MarginType.CROSSED)
#     assert futures_interface.get_margin_type(symbol) == MarginType.CROSSED
#
#
# def test_set_isolated_margin(futures_interface: FuturesExchangeInterface,
#                              symbol: str):
#     if futures_interface.get_exchange_type() == 'ftx_futures':
#         pytest.xfail('FTX Futures does not support isolated margin')
#     futures_interface.set_margin_type(symbol, MarginType.ISOLATED)
#     assert futures_interface.get_margin_type(symbol) == MarginType.ISOLATED


@homogenity_testing
def test_get_open_orders(futures_interface: FuturesExchangeInterface,
                         symbol: str):
    with cancelling_order(futures_interface, symbol) as order:
        open_orders = futures_interface.get_open_orders(symbol)
    assert order in open_orders
    assert all(o.symbol == symbol for o in open_orders)
    return open_orders


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
    errors = []
    resolution = futures_interface.get_funding_rate_resolution()
    for i in range(1, len(history)):
        prev = history[i - 1]
        current = history[i]
        real_res = current['time'] - prev['time']
        if real_res != resolution:
            errors.append(current)
            print(f'wrong resolution in funding rate data: {real_res}, should be {resolution}', file=sys.stderr)
            if len(errors) > 20:
                pytest.fail(f'too many incorrect resolutions: {errors=}')

    return history
