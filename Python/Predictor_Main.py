from multiprocessing import Process, Manager
import time, fbprophet
from decimal import Decimal
from cryptofeed.symbols import binance_symbols
from cryptofeed import FeedHandler
from cryptofeed.callback import BookCallback, FundingCallback, TickerCallback, TradeCallback, FuturesIndexCallback, OpenInterestCallback
from cryptofeed.defines import BID, ASK, BLOCKCHAIN, COINBASE, FUNDING, GEMINI, L2_BOOK, L3_BOOK, OPEN_INTEREST, TICKER, TRADES, VOLUME, FUTURES_INDEX, BOOK_DELTA
from cryptofeed.exchanges import (FTX, Binance, BinanceFutures, Bitfinex, Bitflyer, Bitmax, Bitmex, Bitstamp, Bittrex, Coinbase, Gateio,
                                  HitBTC, Huobi, HuobiDM, HuobiSwap, Kraken, OKCoin, OKEx, Poloniex, Bybit)



class Predictor:
    def __init__(self, exchange_type, initial_state):
        # Shared variables with the processing a manager
        self.__state = Manager().dict(initial_state)
        self.__exchange = exchange_type

    def run(self, args):
        # Start the process
        if (args == None):
            # p = Thread(target=self.main)
            p = Process(target=self.main)
        else:
            # p = Thread(target=self.main, args=args)
            p = Process(target=self.main, args=args)
        p.start()

    async def ticker(feed, symbol, bid, ask, timestamp, receipt_timestamp):
        print(f'Timestamp: {timestamp} Feed: {feed} Pair: {symbol} Bid: {bid} Ask: {ask}')

    async def delta(feed, symbol, delta, timestamp, receipt_timestamp):
        print(
            f'Timestamp: {timestamp} Feed: {feed} Pair: {symbol} Delta Bid Size is {len(delta[BID])} Delta Ask Size is {len(delta[ASK])}')

    async def trade(feed, symbol, order_id, timestamp, side, amount, price, receipt_timestamp):
        assert isinstance(timestamp, float)
        assert isinstance(side, str)
        assert isinstance(amount, Decimal)
        assert isinstance(price, Decimal)
        print(
            f"Timestamp: {timestamp} Cryptofeed Receipt: {receipt_timestamp} Feed: {feed} Pair: {symbol} ID: {order_id} Side: {side} Amount: {amount} Price: {price}")

    async def book(feed, symbol, book, timestamp, receipt_timestamp):
        print(
            f'Timestamp: {timestamp} Cryptofeed Receipt: {receipt_timestamp} Feed: {feed} Pair: {symbol} Book Bid Size is {len(book[BID])} Ask Size is {len(book[ASK])}')

    async def funding(**kwargs):
        print(f"Funding Update for {kwargs['feed']}")
        print(kwargs)

    async def oi(feed, symbol, open_interest, timestamp, receipt_timestamp):
        print(f'Timestamp: {timestamp} Feed: {feed} Pair: {symbol} open interest: {open_interest}')

    async def volume(**kwargs):
        print(f"Volume: {kwargs}")

    async def futures_index(**kwargs):
        print(f"FuturesIndex: {kwargs}")


    def get_state(self):
        return self.__state

    def update_state(self, key, value):
        self.__state[key] = value


    def main(self, args=None):
        # Main loop, running on different thread, data can be exchanged by modifying the "state" variable

        # config = {'log': {'filename': 'demo.log', 'level': 'INFO'}}
        # f = FeedHandler()
        #
        # f.add_feed(f.add_feed(Coinbase(symbols=['BTC-USD'], channels=[TRADES], callbacks={TRADES: TradeCallback(self.trade)})))
        # f.run()

        self.update_state("thomps", 0)
        while True:
            self.update_state("thomps", self.get_state()["thomps"]+1)
            time.sleep(1)