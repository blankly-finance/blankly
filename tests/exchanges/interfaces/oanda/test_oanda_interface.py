import datetime
import time
from datetime import datetime as dt
from pathlib import Path

import pytest
import pytz

from blankly.exchanges.interfaces.oanda.oanda_api import OandaAPI
from blankly.exchanges.interfaces.oanda.oanda_auth import OandaAuth
from blankly.exchanges.interfaces.oanda.oanda_interface import OandaInterface
from blankly.exchanges.interfaces.direct_calls_factory import DirectCallsFactory

timeZ_Ny = pytz.timezone('America/New_York')
MARKET_OPEN = datetime.time(hour=9, minute=0, second=0, tzinfo=timeZ_Ny)
MARKET_CLOSE = datetime.time(hour=17, minute=0, second=0, tzinfo=timeZ_Ny)


@pytest.fixture
def oanda_interface():
    keys_file_path = Path("tests/config/keys.json").resolve()
    settings_file_path = Path("tests/config/settings.json").resolve()

    auth_obj = OandaAuth(str(keys_file_path), "oanda test portfolio")
    _, oanda_interface = DirectCallsFactory.create("oanda", auth_obj, str(settings_file_path))
    return oanda_interface


def test_get_exchange(oanda_interface: OandaInterface) -> None:
    assert oanda_interface.get_exchange_type() == 'oanda'

def test_api() -> None:
    keys_file_path = Path("tests/config/keys.json").resolve()
    settings_file_path = Path("tests/config/settings.json").resolve()

    auth_obj = OandaAuth(str(keys_file_path), "oanda test portfolio")
    api, _ = DirectCallsFactory.create("oanda", auth_obj, str(settings_file_path))
    assert isinstance(api, OandaAPI)
    print(api.get_all_accounts())
    print(api.get_account('101-001-20168332-001'))
    print(api.get_account_summary('101-001-20168332-001'))
    print(api.get_account_instruments('101-001-20168332-001'))
    print(api.get_account_changes('101-001-20168332-001', 3))
