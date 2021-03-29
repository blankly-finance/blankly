#
# Coinbase_Pro/orderbook
# David Caseria
#
# Live order book updated from the Coinbase Websocket Feed

from sortedcontainers import SortedDict
from decimal import Decimal
import pickle

from cbpro.public_client import PublicClient
from cbpro.websocket_client import WebsocketClient


class OrderBook(WebsocketClient):
    def __init__(self, product_id='BTC-USD', log_to=None):
        super(OrderBook, self).__init__(products=product_id)
        self._asks = SortedDict()
        self._bids = SortedDict()
        self._client = PublicClient()
        self._sequence = -1
        self._log_to = log_to
        if self._log_to:
            assert hasattr(self._log_to, 'write')
        self._current_ticker = None

    @property
    def product_id(self):
        ''' Currently OrderBook only supports a single product even though it is stored as a list of products. '''
        return self.products[0]

    def on_open(self):
        self._sequence = -1
        print("-- Subscribed to OrderBook! --\n")

    def on_close(self):
        print("\n-- OrderBook Socket Closed! --")

    def reset_book(self):
        self._asks = SortedDict()
        self._bids = SortedDict()
        res = self._client.get_product_order_book(product_id=self.product_id, level=3)
        for bid in res['bids']:
            self.add({
                'id': bid[2],
                'side': 'buy',
                'price': Decimal(bid[0]),
                'size': Decimal(bid[1])
            })
        for ask in res['asks']:
            self.add({
                'id': ask[2],
                'side': 'sell',
                'price': Decimal(ask[0]),
                'size': Decimal(ask[1])
            })
        self._sequence = res['sequence']

    def on_message(self, message):
        if self._log_to:
            pickle.dump(message, self._log_to)

        sequence = message.get('sequence', -1)
        if self._sequence == -1:
            self.reset_book()
            return
        if sequence <= self._sequence:
            # ignore older messages (e.g. before order book initialization from getProductOrderBook)
            return
        elif sequence > self._sequence + 1:
            self.on_sequence_gap(self._sequence, sequence)
            return

        msg_type = message['type']
        if msg_type == 'open':
            self.add(message)
        elif msg_type == 'done' and 'price' in message:
            self.remove(message)
        elif msg_type == 'match':
            self.match(message)
            self._current_ticker = message
        elif msg_type == 'change':
            self.change(message)

        self._sequence = sequence

    def on_sequence_gap(self, gap_start, gap_end):
        self.reset_book()
        print('Error: messages missing ({} - {}). Re-initializing  book at sequence.'.format(
            gap_start, gap_end, self._sequence))


    def add(self, order):
        order = {
            'id': order.get('order_id') or order['id'],
            'side': order['side'],
            'price': Decimal(order['price']),
            'size': Decimal(order.get('size') or order['remaining_size'])
        }
        if order['side'] == 'buy':
            bids = self.get_bids(order['price'])
            if bids is None:
                bids = [order]
            else:
                bids.append(order)
            self.set_bids(order['price'], bids)
        else:
            asks = self.get_asks(order['price'])
            if asks is None:
                asks = [order]
            else:
                asks.append(order)
            self.set_asks(order['price'], asks)

    def remove(self, order):
        price = Decimal(order['price'])
        if order['side'] == 'buy':
            bids = self.get_bids(price)
            if bids is not None:
                bids = [o for o in bids if o['id'] != order['order_id']]
                if len(bids) > 0:
                    self.set_bids(price, bids)
                else:
                    self.remove_bids(price)
        else:
            asks = self.get_asks(price)
            if asks is not None:
                asks = [o for o in asks if o['id'] != order['order_id']]
                if len(asks) > 0:
                    self.set_asks(price, asks)
                else:
                    self.remove_asks(price)

    def match(self, order):
        size = Decimal(order['size'])
        price = Decimal(order['price'])

        if order['side'] == 'buy':
            bids = self.get_bids(price)
            if not bids:
                return
            assert bids[0]['id'] == order['maker_order_id']
            if bids[0]['size'] == size:
                self.set_bids(price, bids[1:])
            else:
                bids[0]['size'] -= size
                self.set_bids(price, bids)
        else:
            asks = self.get_asks(price)
            if not asks:
                return
            assert asks[0]['id'] == order['maker_order_id']
            if asks[0]['size'] == size:
                self.set_asks(price, asks[1:])
            else:
                asks[0]['size'] -= size
                self.set_asks(price, asks)

    def change(self, order):
        try:
            new_size = Decimal(order['new_size'])
        except KeyError:
            return

        try:
            price = Decimal(order['price'])
        except KeyError:
            return

        if order['side'] == 'buy':
            bids = self.get_bids(price)
            if bids is None or not any(o['id'] == order['order_id'] for o in bids):
                return
            index = [b['id'] for b in bids].index(order['order_id'])
            bids[index]['size'] = new_size
            self.set_bids(price, bids)
        else:
            asks = self.get_asks(price)
            if asks is None or not any(o['id'] == order['order_id'] for o in asks):
                return
            index = [a['id'] for a in asks].index(order['order_id'])
            asks[index]['size'] = new_size
            self.set_asks(price, asks)

        tree = self._asks if order['side'] == 'sell' else self._bids
        node = tree.get(price)

        if node is None or not any(o['id'] == order['order_id'] for o in node):
            return

    def get_current_ticker(self):
        return self._current_ticker

    def get_current_book(self):
        result = {
            'sequence': self._sequence,
            'asks': [],
            'bids': [],
        }
        for ask in self._asks:
            try:
                # There can be a race condition here, where a price point is removed
                # between these two ops
                this_ask = self._asks[ask]
            except KeyError:
                continue
            for order in this_ask:
                result['asks'].append([order['price'], order['size'], order['id']])
        for bid in self._bids:
            try:
                # There can be a race condition here, where a price point is removed
                # between these two ops
                this_bid = self._bids[bid]
            except KeyError:
                continue

            for order in this_bid:
                result['bids'].append([order['price'], order['size'], order['id']])
        return result

    def get_ask(self):
        return self._asks.peekitem(0)[0]

    def get_asks(self, price):
        return self._asks.get(price)

    def remove_asks(self, price):
        del self._asks[price]

    def set_asks(self, price, asks):
        self._asks[price] = asks

    def get_bid(self):
        return self._bids.peekitem(-1)[0]

    def get_bids(self, price):
        return self._bids.get(price)

    def remove_bids(self, price):
        del self._bids[price]

    def set_bids(self, price, bids):
        self._bids[price] = bids