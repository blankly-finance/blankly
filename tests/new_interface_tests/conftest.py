from _pytest.python import Metafunc

from blankly.exchanges.interfaces.abc_base_exchange_interface import ABCBaseExchangeInterface
from blankly.exchanges.interfaces.futures_exchange_interface import FuturesExchangeInterface

from blankly.exchanges.futures.futures_exchange import FuturesExchange

from tests.new_interface_tests.test_utils import FUTURES_EXCHANGES, get_symbols, SPOT_EXCHANGES


def gen_id(arg):
    if isinstance(arg, ABCBaseExchangeInterface):
        return arg.get_exchange_type()
    return arg


def pytest_generate_tests(metafunc: Metafunc):
    interface_params = [p_name for p_name in metafunc.fixturenames if p_name.endswith('interface')]
    if len(interface_params) < 1:
        return  # no interface params is fine

    if len(interface_params) > 1:
        raise Exception('maximum one interface parameter per test function')

    interface_param = interface_params[0]

    if interface_param == 'futures_interface':
        interfaces = [ex.interface for ex in FUTURES_EXCHANGES]
    elif interface_param == 'spot_interface':
        interfaces = [ex.interface for ex in SPOT_EXCHANGES]
    elif interface_param == 'interface':
        interfaces = [ex.interface for ex in FUTURES_EXCHANGES + SPOT_EXCHANGES]
    else:
        raise Exception('invalid interface type: ' + interface_param)

    if 'symbol' in metafunc.fixturenames:
        vals = [(interface, symbol) for interface in interfaces
                for symbol in get_symbols(interface)]
        metafunc.parametrize(f'{interface_param},symbol', vals, ids=gen_id)
    else:
        metafunc.parametrize(interface_param, interfaces, ids=gen_id)
