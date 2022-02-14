import time

import pandas as pd
from blankly.exchanges.interfaces.kraken.kraken_api import API as KrakenAPI
from typing import List
import warnings

import blankly.utils.time_builder
import blankly.utils.utils as utils
import blankly.exchanges.interfaces.kraken.kraken_interface_utils as interface_utils
from blankly.exchanges.interfaces.exchange_interface import ExchangeInterface
from blankly.exchanges.orders.limit_order import LimitOrder
from blankly.exchanges.orders.market_order import MarketOrder
from blankly.exchanges.orders.stop_limit import StopLimit
from blankly.utils.exceptions import APIException, InvalidOrder


class KrakenInterface(ExchangeInterface):

    # NOTE, kraken has no sandbox mode
    def __init__(self, authenticated_API: KrakenAPI, preferences_path: str):
        super().__init__('kraken', authenticated_API, preferences_path, valid_resolutions=None)

        self.account_levels_to_max_open_orders = {
            "Starter": 60,
            "Express": 60,
            "Intermediate": 80,
            "Pro": 225
        }

    def init_exchange(self):
        pass

        """
        'get_products': [
                ["symbol", str],
                ["base_asset", str],
                ["quote_asset", str],
                ["base_min_size", float],
                ["base_max_size", float],
                ["base_increment", float]
            ],
        """

        """
        
        NOTE:
        This method might behave incorrectly as it sets the symbol as 
        wsname (returned by Kraken API). This was chosen as it most
        closely fits in with the symbol names used by the rest of the 
        package, but may be less stable as it may or may not be 
        intended to be fully relied upon.
        
        """

    def get_products(self) -> list:

        needed_asset_pairs = []
        needed = self.needed["get_products"]
        asset_pairs: List[dict] = self.get_calls().asset_pairs()
        for asset_id, asset_pair in asset_pairs.items():
            asset_pair["symbol"] = asset_pair["wsname"].replace('/', '-')
            asset_pair["base_asset"] = asset_pair.pop("base")
            asset_pair["quote_asset"] = asset_pair.pop("quote")
            asset_pair["base_min_size"] = asset_pair.pop("ordermin")
            asset_pair["base_max_size"] = 99999999999
            asset_pair["base_increment"] = 10 ** (-1 * float(asset_pair.pop("lot_decimals")))
            asset_pair["kraken_id"] = asset_id
            needed_asset_pairs.append(utils.isolate_specific(needed, asset_pair))

        return needed_asset_pairs

    # NOTE: implement this
    def get_account(self, symbol=None):
        symbol = super().get_account(symbol)

        positions = self.calls.list_positions()
        positions_dict = utils.AttributeDict({})

        for position in positions:
            curr_symbol = position.pop('symbol')
            positions_dict[curr_symbol] = utils.AttributeDict({
                'available': float(position.pop('vol')),
                'hold': 0.0
            })

        symbols = list(positions_dict.keys())
        # Catch an edge case bug that if there are no positions it won't try to snapshot
        if len(symbols) != 0:
            open_orders = self.calls.list_orders(status='open', symbols=symbols)
            snapshot_price = self.calls.get_snapshots(symbols=symbols)
        else:
            open_orders = []
            snapshot_price = {}

        # now grab the available cash in the account
        account = self.calls.get_account()
        positions_dict['USD'] = utils.AttributeDict({
            'available': float(account['buying_power']),
            'hold': 0.0
        })

        for order in open_orders:
            curr_symbol = order['symbol']
            if order['side'] == 'buy':  # buy orders only affect USD holds
                if order['qty']:  # this case handles qty market buy and limit buy
                    if order['type'] == 'limit':
                        dollar_amt = float(order['qty']) * float(order['limit_price'])
                    elif order['type'] == 'market':
                        dollar_amt = float(order['qty']) * snapshot_price[curr_symbol]['latestTrade']['p']
                    else:  # we don't have support for stop_order, stop_limit_order
                        dollar_amt = 0.0
                else:  # this is the case for notional market buy
                    dollar_amt = float(order['notional'])

                # In this case we don't have to subtract because the buying power is the available money already
                # we just need to add to figure out how much is actually on limits
                # positions_dict['USD']['available'] -= dollar_amt

                # So just add to our hold
                positions_dict['USD']['hold'] += dollar_amt

            else:
                if order['qty']:  # this case handles qty market sell and limit sell
                    qty = float(order['qty'])
                else:  # this is the case for notional market sell, calculate the qty with cash/price
                    qty = float(order['notional']) / snapshot_price[curr_symbol]['latestTrade']['p']

                positions_dict[curr_symbol]['available'] -= qty
                positions_dict[curr_symbol]['hold'] += qty

        # Note that now __unique assets could be uninitialized:
        if self.__unique_assets is None:
            self.init_exchange()

        for i in self.__unique_assets:
            if i not in positions_dict:
                positions_dict[i] = utils.AttributeDict({
                    'available': 0.0,
                    'hold': 0.0
                })

        if symbol is not None:
            if symbol in positions_dict:
                return utils.AttributeDict({
                    'available': float(positions_dict[symbol]['available']),
                    'hold': float(positions_dict[symbol]['hold'])
                })
            else:
                raise KeyError('Symbol not found.')

        if symbol == 'USD':
            return utils.AttributeDict({
                'available': positions_dict['USD']['available'],
                'hold': positions_dict['USD']['hold']
            })

        return positions_dict

    def market_order(self, symbol: str, side: str, size: float):
        """
        Needed:
        'market_order': [
                ["symbol", str],
                ["id", str],
                ["created_at", float],
                ["size", float],
                ["status", str],
                ["type", str],
                ["side", str]
            ],
        """
        symbol = interface_utils.blankly_symbol_to_kraken_symbol(symbol)
        response = self.get_calls().add_order(symbol, side, "market", 0, size)

        txid = response["txid"]
        order_info = self.get_calls().query_orders(txid=txid)

        order_info["symbol"] = symbol
        order_info["id"] = txid
        order_info["created_at"] = order_info.pop("opentm")
        order_info["size"] = size
        order_info["type"] = "market"
        order_info["side"] = order_info["descr"]["type"]

        order = {
            'size': size,
            'side': side,
            'symbol': symbol,
            'type': 'market'
        }

        return MarketOrder(order, order_info, self)

    def limit_order(self, symbol: str, side: str, price: float, size: float):
        symbol = interface_utils(symbol)
        response = self.get_calls().add_order(symbol, side, "market", price, size)
        txid = response["txid"]
        order_info = self.get_calls().query_orders(txid=txid)

        order_info["symbol"] = symbol
        order_info["id"] = txid
        order_info["created_at"] = order_info.pop("opentm")
        order_info["size"] = size
        order_info["type"] = "market"
        order_info["side"] = order_info["descr"]["type"]

        order = {
            'size': size,
            'side': side,
            'symbol': symbol,
            'type': 'market'
        }

        return LimitOrder(order, order_info, self)

    def cancel_order(self, symbol: str, order_id: str):
        return self.get_calls().cancel_order(order_id)

    def get_open_orders(self, symbol: str = None) -> list:
        """
        List open orders.
        Args:
            symbol (optional) (str): Asset such as BTC-USD
        """
        response = self.get_calls().open_orders(symbol)["open"]
        response_needed_fulfilled = []
        if (len(response) == 0):
            return []

        for open_order_id, open_order_info in response.items():
            utils.pretty_print_JSON(f"json: {response}", actually_print=True)

            # Needed:
            # 'get_open_orders': [  # Key specificity changes based on order type
            #     ["id", str],
            #     ["price", float],
            #     ["size", float],
            #     ["type", str],
            #     ["side", str],
            #     ["status", str],
            #     ["product_id", str]
            # ],

            open_order_info['id'] = open_order_id
            open_order_info["size"] = open_order_info.pop("vol")
            open_order_info["type"] = open_order_info["descr"].pop("ordertype")
            open_order_info["side"] = open_order_info["descr"].pop("type")
            open_order_info['product_id'] = interface_utils.kraken_symbol_to_blankly_symbol(
                open_order_info["descr"].pop('pair'))
            open_order_info['created_at'] = open_order_info.pop('opentm')

            if open_order_info["type"] == "limit":
                needed = self.choose_order_specificity("limit")
                open_order_info['time_in_force'] = "GTC"
                open_order_info['price'] = float(open_order_info["descr"].pop("price"))
            elif open_order_info["type"] == "market":
                needed = self.choose_order_specificity("market")

            open_order_info = utils.isolate_specific(needed, open_order_info)

            response_needed_fulfilled.append(open_order_info)

        return response_needed_fulfilled

    # 'get_order': [
    #     ["product_id", str],
    #     ["id", str],
    #     ["price", float],
    #     ["size", float],
    #     ["type", str],
    #     ["side", str],
    #     ["status", str],
    #     ["funds", float]
    # ],

    def get_order(self, symbol: str, order_id: str) -> dict:
        """
        Get a certain order
        Args:
            symbol: Asset that the order is under
            order_id: The unique ID of the order.
        """
        response = self.get_calls().query_orders(txid=order_id)[order_id]
        utils.pretty_print_JSON(response, actually_print=True)

        order_type = response["descr"].pop("ordertype")

        needed = self.choose_order_specificity(order_type)

        response["id"] = order_id
        response['type'] = order_type
        response['symbol'] = interface_utils.kraken_symbol_to_blankly_symbol(response['descr']['pair'])
        response['created_at'] = response.pop('opentm')
        response['price'] = response['descr'].pop('price')
        response['size'] = response.pop("vol")
        response['side'] = response["descr"].pop("type")
        # NOTE, what is funds in needed?

        if order_type == "limit":
            response['time_in_force'] = "GTC"

        response = utils.isolate_specific(needed, response)
        return response

    # NOTE fees are dependent on asset pair, so this is a required parameter to call the function
    def get_fees(self) -> dict:
        asset_symbol = "XBTUSDT"
        size = 1
        asset_pair_info = self.get_calls().asset_pairs()

        fees_maker: List[List[float]] = asset_pair_info[(asset_symbol)]["fees_maker"]
        fees_taker: List[List[float]] = asset_pair_info[(asset_symbol)]["fees"]

        # fees_maker: List[List[float]] = asset_pair_info[interface_utils.blankly_symbol_to_kraken_symbol(asset_symbol)]["fees_maker"]
        # fees_taker: List[List[float]] = asset_pair_info[interface_utils.blankly_symbol_to_kraken_symbol(asset_symbol)]["fees"]

        for volume_fee in reversed(fees_maker):
            if size > volume_fee[0]:
                fee_maker = volume_fee[1]

        for volume_fee in reversed(fees_taker):
            if size > volume_fee[0]:
                fee_taker = volume_fee[1]

        return {
            "maker_fee_rate": fee_maker,
            "taker_fee_rate": fee_taker,
        }

    def get_product_history(self, symbol, epoch_start, epoch_stop, resolution) -> pd.DataFrame:

        # symbol = interface_utils.blankly_symbol_to_kraken_symbol(symbol)
        symbol = "XBTUSD"
        accepted_grans = [60, 300, 900, 1800, 3600, 14400, 86400, 604800, 1296000]

        if resolution not in accepted_grans:
            utils.info_print("Granularity is not an accepted granularity...rounding to nearest valid value.")
            resolution = accepted_grans[min(range(len(accepted_grans)),
                                            key=lambda i: abs(accepted_grans[i] - resolution))]

        # kraken processes resolution in seconds, so the granularity must be divided by 60
        product_history = self.get_calls().ohlc(symbol, interval=(resolution / 60), since=epoch_start)
        symbol = "XXBTZUSD"
        historical_data_raw = product_history[symbol]
        historical_data_block = []
        num_intervals = len(historical_data_raw)

        for i, interval in enumerate(historical_data_raw):

            time = interval[0]
            open_ = interval[1]
            high = interval[2]
            low = interval[3]
            close = interval[4]
            volume = interval[5]

            if time > epoch_stop:
                break

            historical_data_block.append([time, low, high, open_, close, volume])

            utils.update_progress(i / num_intervals)

        print("\n")
        df = pd.DataFrame(historical_data_block, columns=['time', 'low', 'high', 'open', 'close', 'volume'])
        df_start = df["time"][0]
        if df_start > epoch_start:
            warnings.warn(
                f"Due to kraken's API limitations, we could only collect OHLC data as far back as unix epoch {df_start}")

        df = df.astype({
            'open': float,
            'high': float,
            'low': float,
            'close': float,
            'volume': float
        })
        return df

    def get_order_filter(self, symbol: str) -> dict:

        symbol = "XBTUSDT"
        kraken_symbol = symbol
        # kraken_symbol = interface_utils.blankly_symbol_to_kraken_symbol(symbol)

        asset_info = self.get_calls().asset_pairs(pairs=kraken_symbol)

        price = self.get_calls().ticker(kraken_symbol)[kraken_symbol]["c"][0]

        # max_orders = self.account_levels_to_max_open_orders[self.user_preferences["settings"]["kraken"]["account_type"]]

        return {
            "symbol": symbol,
            "base_asset": asset_info[kraken_symbol]["wsname"].split("/")[0],
            "quote_asset": asset_info[kraken_symbol]["wsname"].split("/")[1],
            "max_orders": self.account_levels_to_max_open_orders[
                self.user_preferences["settings"]["kraken"]["account_type"]],
            "limit_order": {
                "base_min_size": asset_info[kraken_symbol]["ordermin"],
                "base_max_size": 999999999,
                "base_increment": asset_info[kraken_symbol]["lot_decimals"],
                "price_increment": asset_info[kraken_symbol]["pair_decimals"],
                "min_price": float(asset_info[kraken_symbol]["ordermin"]) * float(price),
                "max_price": 999999999,
            },
            "market_order": {
                "base_min_size": asset_info[kraken_symbol]["ordermin"],
                "base_max_size": 999999999,
                "base_increment": asset_info[kraken_symbol]["lot_decimals"],
                "quote_increment": asset_info[kraken_symbol]["pair_decimals"],
                "buy": {
                    "min_funds": 0,
                    "max_funds": 999999999,
                },
                "sell": {
                    "min_funds": 0,
                    "max_funds": 999999999
                },

            },
            "exchange_specific": {}

        }

    def get_price(self, symbol: str) -> float:
        """
        Returns just the price of a symbol.
        Args:
            symbol: The asset such as (BTC-USD, or MSFT)
        """
        symbol = "XBTUSDT"
        # symbol = interface_utils.blankly_symbol_to_kraken_symbol(symbol)

        resp = self.get_calls().ticker(symbol)

        opening_price = float(resp[symbol]["o"])
        volume_weighted_average_price = float(resp[symbol]["p"][0])
        last_price = float(resp[symbol]["c"][0])

        return volume_weighted_average_price
