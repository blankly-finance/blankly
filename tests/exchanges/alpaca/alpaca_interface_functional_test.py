from Blankly.auth.Alpaca.auth import AlpacaAuth
from Blankly.auth.direct_calls_factory import InterfaceFactory
import pytest

from Blankly.exchanges.Alpaca.alpaca_api_interface import AlpacaInterface
from tests.helpers.comparisons import is_sub_dict
from pathlib import Path

@pytest.fixture
def alpaca_interface() -> None:
    keys_file_path = Path("tests/config/keys.json").resolve()
    settings_file_path = Path("tests/config/settings.json").resolve()

    auth_obj = AlpacaAuth(keys_file_path, "alpaca test portfolio")
    _, alpaca_interface = InterfaceFactory.create("alpaca", auth_obj, settings_file_path)
    return alpaca_interface


def test_get_exchange(alpaca_interface: AlpacaInterface) -> None:
    assert alpaca_interface.get_exchange_type() == 'alpaca'