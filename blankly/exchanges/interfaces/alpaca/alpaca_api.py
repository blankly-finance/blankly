"""
    Alpaca API creation definition.
    Copyright (C) 2021 Arun Annamalai

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

import os

import alpaca_trade_api

from blankly.exchanges.auth.abc_auth import ABCAuth

APCA_API_LIVE_URL = "https://api.alpaca.markets"
APCA_API_PAPER_URL = "https://paper-api.alpaca.markets"


def create_alpaca_client(auth: ABCAuth, sandbox_mode=True):
    if sandbox_mode:
        api_url = APCA_API_PAPER_URL
    else:
        api_url = APCA_API_LIVE_URL

    return alpaca_trade_api.REST(auth.keys['API_KEY'], auth.keys['API_SECRET'], api_url, 'v2', raw_data=True)


class API:
    def __init__(self, auth: ABCAuth, paper_trading=True):
        if paper_trading:
            self.__api_url = APCA_API_PAPER_URL
        else:
            self.__api_url = APCA_API_LIVE_URL

        self.alp_client = alpaca_trade_api.REST(auth.keys['API_KEY'], auth.keys['API_SECRET'], self.__api_url, 'v2')


api = os.getenv("ALPACA_PUBLIC")
secret = os.getenv("ALPACA_PRIVATE")
