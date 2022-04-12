"""
    Simple utility functions that enable more robust testing
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
import datetime


def get_valid_symbol(exchange: str):
    if exchange == 'binance':
        return 'BTC-USDT'
    elif exchange == 'okx':
        return 'BTC-USDT'
    elif exchange == 'coinbase_pro':
        return 'BTC-USD'
    elif exchange == 'alpaca':
        return 'AAPL'
    elif exchange == 'oanda':
        return 'EUR-USD'
    elif exchange == 'ftx':
        return 'BTC-USD'
    elif exchange == 'kucoin':
        return 'ETH-USDT'
    else:
        raise LookupError("Specified exchange not found.")


def forex_market_open():
    now = datetime.datetime.now()
    # friday == 4
    # saturday == 5
    # TODO Technically it resumes at 5pm sunday but I don't handle that
    if now.weekday() >= 5:
        return False
    elif now.weekday() >= 4 and now.hour >= 17:
        return False
    else:
        return True
