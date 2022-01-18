"""
    Unit tests for validating crypto behaviors
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
import time

import blankly


def test_crypto_websocket():
    test = CryptoWebsockets()

    assert test.passed


class CryptoWebsockets:

    def __init__(self):
        self.validated_responses = {
            'orderbook': {
                'coinbase_pro': False,
                'binance': False
            },
            'prices': {
                'coinbase_pro': False,
                'binance': False,
                'ftx':  False,
            }
        }

        kwargs = {'keys_path': './tests/config/keys.json',
                  'settings_path': "./tests/config/settings.json"}
        # Create an exchange to reference the settings.json
        blankly.CoinbasePro(**kwargs)

        self.price_manager = blankly.TickerManager('coinbase_pro', 'BTC-USD')
        self.orderbook_manager = blankly.OrderbookManager('coinbase_pro', 'BTC-USD')

        self.passed = False

        self.test_websockets()

    def test_websockets(self):

        self.price_manager.create_ticker(self.coinbase_price, override_symbol='BTC-USD',
                                         override_exchange='coinbase_pro')

        # Subscribe to a bunch with binance
        self.price_manager.create_ticker(self.binance_price, override_symbol='BTC-USDT', override_exchange='binance')
        self.price_manager.create_ticker(self.binance_price, override_symbol='ETH-USDT', override_exchange='binance')

        self.price_manager.create_ticker(self.ftx_price, override_symbol='BTC-USD', override_exchange='ftx')

        self.orderbook_manager.create_orderbook(self.coinbase_orderbook, override_symbol='BTC-USD',
                                                override_exchange='coinbase_pro')

        self.orderbook_manager.create_orderbook(self.binance_orderbook, override_symbol='BTC-USDT',
                                                override_exchange='binance')

        if self.timeout(180):
            self.passed = True

    def timeout(self, start_at: int):
        def check_responses() -> bool:
            for i in self.validated_responses['orderbook']:
                if not self.validated_responses['orderbook'][i]:
                    return False

            for i in self.validated_responses['prices']:
                if not self.validated_responses['prices'][i]:
                    return False

            return True

        while start_at > 0:
            # It can pass if it's valid within here
            if check_responses():
                assert True
                return True
            time.sleep(1)
            start_at -= 1

        # Better exit before here
        # If this is thrown then the websockets aren't returning values
        print(blankly.utils.pretty_print_json(self.validated_responses))
        assert False

    @staticmethod
    def validate_price_event(event: dict):
        try:
            assert 'symbol' in event
            assert 'price' in event
            assert 'time' in event
            assert 'trade_id' in event
            assert 'size' in event
            return True
        except AssertionError:
            return False

    @staticmethod
    def validate_orderbook_event(event: dict):
        try:
            # Validate the keys
            assert (set(event.keys()) == {'bids', 'asks'})

            # Validate the internal types
            assert (isinstance(event['bids'][0], tuple))
            assert (isinstance(event['asks'][0], tuple))

            return True
        except AssertionError:
            return False

    """
    These can async validate each response
    """
    def coinbase_price(self, message):
        if self.validate_price_event(message):
            self.validated_responses['prices']['coinbase_pro'] = True
            self.price_manager.close_websocket('BTC-USD', 'coinbase_pro')

    def binance_price(self, message):
        if self.validate_price_event(message):
            self.validated_responses['prices']['binance'] = True
            self.price_manager.close_websocket('BTC-USDT', 'binance')
            self.price_manager.close_websocket('ETH-USDT', 'binance')

    def ftx_price(self, message):
        if self.validate_price_event(message):
            self.validated_responses['prices']['ftx'] = True
            self.price_manager.close_websocket('BTC-USD', 'ftx')

    """
    These can async validate each response
    """
    def coinbase_orderbook(self, message):
        if self.validate_orderbook_event(message):
            self.validated_responses['orderbook']['coinbase_pro'] = True
            self.orderbook_manager.close_websocket('BTC-USD', 'coinbase_pro')

    def binance_orderbook(self, message):
        if self.validate_orderbook_event(message):
            self.validated_responses['orderbook']['binance'] = True
            self.orderbook_manager.close_websocket('BTC-USDT', 'binance')
