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

import alpaca_trade_api

from blankly.exchanges.auth.auth_constructor import AuthConstructor

live_url = "https://api.alpaca.markets"
paper_url = "https://paper-api.alpaca.markets"


def create_alpaca_client(auth: AuthConstructor, sandbox_mode=True):
    if sandbox_mode:
        api_url = paper_url
    else:
        api_url = live_url

    return alpaca_trade_api.REST(auth.keys['API_KEY'], auth.keys['API_SECRET'], api_url, 'v2', raw_data=True)


# class API:
#     def __init__(self, auth: AuthConstructor, paper_trading=True):
#         if paper_trading:
#             self.__api_url = APCA_API_PAPER_URL
#         else:
#             self.__api_url = APCA_API_LIVE_URL
#
#         self.alp_client = alpaca_trade_api.REST(auth.keys['API_KEY'], auth.keys['API_SECRET'], self.__api_url, 'v2')
#
