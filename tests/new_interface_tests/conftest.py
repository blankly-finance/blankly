from _pytest.python import Metafunc
from blankly.exchanges.interfaces.futures_exchange_interface import FuturesExchangeInterface

from blankly.exchanges.futures.futures_exchange import FuturesExchange

from tests.new_interface_tests.test_utils import FUTURES_EXCHANGES, SYMBOLS


def gen_id(arg):
    if isinstance(arg, FuturesExchange):
        return arg.get_type()
    elif isinstance(arg, FuturesExchangeInterface):
        return arg.get_exchange_type()
    return arg


def pytest_generate_tests(metafunc: Metafunc):
    if 'futures_interface' in metafunc.fixturenames:
        interfaces = [ex.interface for ex in FUTURES_EXCHANGES]
        if 'symbol' in metafunc.fixturenames:
            vals = [(interface, symbol) for interface in interfaces
                    for symbol in SYMBOLS[interface.get_exchange_type()]]
            metafunc.parametrize('futures_interface,symbol', vals, ids=gen_id)
        else:
            metafunc.parametrize('futures_interface', interfaces, ids=gen_id)

