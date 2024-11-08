"""
    __init__ file to give the module access to the libraries.
    Copyright (C) 2021  Emerson Dove

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import blankly.utils.utils
import blankly.data as data
from blankly.exchanges.interfaces.coinbase_pro.coinbase_pro import CoinbasePro
from blankly.exchanges.interfaces.binance.binance import Binance
from blankly.exchanges.interfaces.alpaca.alpaca import Alpaca
from blankly.exchanges.interfaces.oanda.oanda import Oanda
from blankly.exchanges.interfaces.kucoin.kucoin import Kucoin
from blankly.exchanges.interfaces.ftx.ftx import FTX
from blankly.exchanges.interfaces.okx.okx import Okx
from blankly.exchanges.interfaces.paper_trade.paper_trade import PaperTrade
from blankly.exchanges.interfaces.keyless.keyless import KeylessExchange
from blankly.frameworks.strategy import Strategy as Strategy
from blankly.frameworks.model.model import Model as Model
from blankly.frameworks.strategy import StrategyState as StrategyState
from blankly.frameworks.screener.screener import Screener
from blankly.frameworks.screener.screener_state import ScreenerState

from blankly.exchanges.managers.ticker_manager import TickerManager
from blankly.exchanges.managers.orderbook_manager import OrderbookManager
from blankly.exchanges.managers.general_stream_manager import GeneralManager
from blankly.exchanges.interfaces.abc_exchange_interface import ABCExchangeInterface as Interface
from blankly.frameworks.multiprocessing.blankly_bot import BlanklyBot
from blankly.utils.utils import trunc
import blankly.utils.utils as utils
from blankly.utils.scheduler import Scheduler
import blankly.indicators as indicators
from blankly.utils import time_builder

from blankly.enums import Side, OrderType, OrderStatus, TimeInForce

from blankly.deployment.reporter_headers import Reporter as __Reporter_Headers

is_deployed = False
_screener_runner = None

_backtesting = blankly.utils.check_backtesting()
try:
    from blankly_external import Reporter as __Reporter

    reporter = __Reporter
    is_deployed = True
except ImportError:
    reporter = __Reporter_Headers()
