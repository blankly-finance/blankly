"""
    Websocket feeds need to be modular due to the subscription methods, this provides dynamic management.
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

from Blankly.exchanges.Binance.Binance_Tickers import Tickers


def create_ticker_websocket(currency_pair, log=None):
    return Tickers()


class WebsocketAbstraction:
    def __init__(self, subscription_feed, callback, log=None):
        pass
