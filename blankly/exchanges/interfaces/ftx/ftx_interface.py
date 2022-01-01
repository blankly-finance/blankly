import pandas
from blankly.exchanges.interfaces.exchange_interface import ExchangeInterface
from blankly.exchanges.orders.market_order import MarketOrder
from blankly.exchanges.orders.limit_order import LimitOrder
from blankly.exchanges.interfaces.ftx.ftx_api import FTXAPI
import blankly.utils.utils as utils
import json
import copy
from typing import List
#
class FTXInterface(ExchangeInterface):
    
    #preferences path currently unused (note, FTX has no sandbox mode)
    def __init__(self, authenticated_API: FTXAPI, preferences_path: str):
        super().__init__('ftx', authenticated_API, preferences_path, valid_resolutions=None)

    def init_exchange(self):

        """
            Attempts an API call. If API key is invalid, this 
            method will throw another error specifying that it 
            was due to invalid FTX API keys 
        """
        try:
            self.get_calls().get_account_info()
        except Exception as e:
            if str(e) == "Not logged in: Invalid API key":
                raise LookupError("Unable to connect to FTX US: Invalid API Key")
            else:
                raise e

    """
    needed:
    ---
    'get_products': [
                ["symbol", str],
                ["base_asset", str],
                ["quote_asset", str],
                ["base_min_size", float],
                ["base_max_size", float],
                ["base_increment", float]
            ],

    provided:
    ---
    {
            "name": "ABNB/USD",
            "enabled": true,
            "postOnly": false,
            "priceIncrement": 0.005, //NOTE: api call returns both price and size increment. base_increment is currently set to size, however this may not be the expected result
            "sizeIncrement": 0.025,
            "minProvideSize": 0.025,
            "last": 169.09,
            "bid": 170.68,
            "ask": 171.205,
            "price": 170.68,
            "type": "spot",
            "baseCurrency": "ABNB",
            "quoteCurrency": "USD",
            "underlying": null,
            "restricted": true,
            "tokenizedEquity": true,
            "highLeverageFeeExempt": true,
            "change1h": -0.003590297440088736,
            "change24h": 0.00014649438926489115,
            "changeBod": -0.00367754363434709,
            "quoteVolume24h": 12.76575,
            "volumeUsd24h": 12.76575
        },
    """
    #only includes markets of type "spot" (i.e. excludes futures) 
    def get_products(self) -> list:

        needed = self.needed['get_products']

        
        products : List[dict] = self.get_calls().list_markets()

        end_products = []

        for index, product in enumerate(products):
            if product['type'] == "spot":
                product['symbol'] = product.pop('name')
                product['base_asset'] = product.pop('baseCurrency')
                product['quote_asset'] = product.pop('quoteCurrency')
                product['base_min_size'] = product.pop('minProvideSize')
                product['base_max_size'] = 99999999
                product['base_increment'] = product.pop('sizeIncrement')

                product = utils.isolate_specific(needed, product)

                end_products.append(product)

            else:
                #note: we are not including futures in the result
                pass
                


        return end_products

    
    def get_account(self, symbol: str = None) -> utils.AttributeDict:
        """
        Get all assets in an account, or sort by symbol/account_id
        Args:
            symbol (Optional): Filter by particular symbol

            These arguments are mutually exclusive

        TODO add return example
        """

        symbol = super().get_account(symbol = symbol)

        needed = self.needed['get_account']
        parsed_dictionary = utils.AttributeDict({})
        balances: List[dict] = self.get_calls().get_balances()

        if symbol is not None:
            for account in balances:
                if account["coin"] == symbol:
                    account['hold'] = account['total'] - account['free']
                    account['currency'] = account.pop('coin')
                    account['available'] = account.pop('free')
                    parsed_value = utils.isolate_specific(needed, account)
                    requested_account = utils.AttributeDict({
                        'available': parsed_value['available'],
                        'hold': parsed_value['hold']
                    })
                    return requested_account
            raise ValueError("Symbol not found")
        
        else:
            for account in balances:
                account['hold'] = account['total'] - account['free']
                account['currency'] = account.pop('coin')
                account['available'] = account.pop('free')
                parsed_dictionary[account['currency']] = utils.AttributeDict({
                    'available': float(account['available']),
                    'hold': float(account['hold'])
                })
            return parsed_dictionary

    """
    needed:

    'market_order': [
                ["symbol", str],
                ["id", str],
                ["created_at", float],
                ["size", float],
                ["status", str],
                ["type", str],
                ["side", str]
            ],

    response: 

    {
    "createdAt": "2019-03-05T09:56:55.728933+00:00",
    "filledSize": 0,
    "future": "XRP-PERP",
    "id": 9596912,
    "market": "XRP-PERP",
    "price": 0.306525,
    "remainingSize": 31431,
    "side": "sell",
    "size": 31431,
    "status": "open",
    "type": "limit",
    "reduceOnly": false,
    "ioc": false,
    "postOnly": false,
    "clientId": null,
    }
    """

    def market_order(self, symbol: str, side: str, size: float) -> MarketOrder:
        """
        Used for buying or selling market orders
        Args:
            symbol: asset to buy
            side: buy/sell
            size: desired amount of base asset to use
        """
        needed = self.needed['market_order']

        response = self.get_calls().place_order(symbol, side, None, size, order_type = "market")

        response["symbol"] = response.pop("market")
        response["created_at"] = utils.epoch_from_ISO8601(response.pop("createdAt"))

        response = utils.isolate_specific(needed, response)

        order = {
            'size': size,
            'side': side,
            'symbol': symbol,
            'type': 'market'
        }

        return MarketOrder(order, response, self)
    
    """
    needed

    'limit_order': [
                ["symbol", str],
                ["id", str],
                ["created_at", float],
                ["price", float],
                ["size", float],
                ["status", str],
                ["time_in_force", str],
                ["type", str],
                ["side", str]
                ],

    response

    {
    "success": true,
    "result": {
        "createdAt": "2019-03-05T09:56:55.728933+00:00",
        "filledSize": 0,
        "future": "XRP-PERP",
        "id": 9596912,
        "market": "XRP-PERP",
        "price": 0.306525,
        "remainingSize": 31431,
        "side": "sell",
        "size": 31431,
        "status": "open",
        "type": "limit",
        "reduceOnly": false,
        "ioc": false,
        "postOnly": false,
        "clientId": null,
        }
    }
    """

    def limit_order(self,
                    symbol: str,
                    side: str,
                    price: float,
                    size: float) -> LimitOrder:
        """
        Used for buying or selling limit orders
        Args:
            symbol: asset to buy
            side: buy/sell
            price: price to set limit order
            size: amount of asset (like BTC) for the limit to be valued
        """
        needed = self.needed['limit_order']
        response = self.get_calls().place_order(symbol, side, price, size, order_type = "limit")

        order = {
            'size': size,
            'side': side,
            'price': price,
            'symbol': symbol,
            'type': 'limit'
        }

        response["symbol"] = response.pop("market")
        response["created_at"] = utils.epoch_from_ISO8601(response.pop("createdAt"))
        response["time_in_force"] = "GTC"
        response = utils.isolate_specific(needed, response)

        return LimitOrder(order, response, self)
    

#    def stop_limit(self, symbol, side, stop_price, limit_price, size, stop = 'loss'):


    def cancel_order(self, symbol: str, order_id: str) -> dict:
        """
        Cancel an order on a particular symbol & order id

        Args:
            symbol: This is the asset id that the order is under
            order_id: The unique ID of the order.

        """
        self.get_calls().cancel_order(order_id)
        return order_id

    """
    [
        {
        "createdAt": "2019-03-05T09:56:55.728933+00:00",
        "filledSize": 10,
        "future": "XRP-PERP",
        "id": 9596912,
        "market": "XRP-PERP",
        "price": 0.306525,
        "avgFillPrice": 0.306526,
        "remainingSize": 31421,
        "side": "sell",
        "size": 31431,
        "status": "open",
        "type": "limit",
        "reduceOnly": false,
        "ioc": false,
        "postOnly": false,
        "clientId": null
        },
        {
            ...
        },
        ...
        {
            ...
        }

    ]
    """
    def get_open_orders(self, symbol: str = None) -> list:
        """
        List open orders.
        Args:
            symbol (optional) (str): Asset such as BTC-USD
        """
        response = self.get_calls().get_open_orders(symbol)
        if(len(response) == 0):
            return []
        
        needed = self.choose_order_specificity(response['type'])

        for open_order in response:
            open_order['symbol'] = open_order.pop('market')
            if open_order["type"] == "limit":
                open_order['time_in_force'] = "GTC"
            open_order['created_at'] = open_order.epoch_from_ISO8601(response.pop('createdAt'))
            open_order = utils.isolate_specific(needed, open_order)
        
        return response

    """
    {
        "createdAt": "2019-03-05T09:56:55.728933+00:00",
        "filledSize": 10,
        "future": "XRP-PERP",
        "id": 9596912,
        "market": "XRP-PERP",
        "price": 0.306525,
        "avgFillPrice": 0.306526,
        "remainingSize": 31421,
        "side": "sell",
        "size": 31431,
        "status": "open",
        "type": "limit",
        "reduceOnly": false,
        "ioc": false,
        "postOnly": false,
        "clientId": "your_client_order_id"
    }
    """

    def get_order(self, symbol: str, order_id: str) -> dict:
        """
        Get a certain order
        Args:
            symbol: Asset that the order is under
            order_id: The unique ID of the order.
        """
        response = self.get_calls().get_order_by_id(order_id)

        needed = self.choose_order_specificity(response["type"])

        
        response['symbol'] = response.pop('market')
        response['created_at'] = utils.epoch_from_ISO8601(response.pop('createdAt'))

        if response["type"] == "limit":
            response['time_in_force'] = "GTC"

        response = utils.isolate_specific(needed, response)
        return response

    
    def get_fees(self) -> dict:
        """
        Get market fees

        lot of unnecessary info in exchange-specific section

        TODO: remove everything truly irrelevant to fees
        """

        needed = self.needed['get_fees']
        account_info = self.get_calls().get_account_info()
        account_info['maker_fee_rate'] = account_info.pop('makerFee')
        account_info['taker_fee_rate'] = account_info.pop('takerFee')
        account_info = utils.isolate_specific(needed, account_info)
        

        return account_info

    
    def get_product_history(self, symbol: str, epoch_start: float, epoch_stop: float, resolution) -> pandas.DataFrame:
        """
        Returns the product history from an exchange
        Args:
            symbol: The asset such as (BTC-USD, or MSFT)
            epoch_start: Time to begin download
            epoch_stop: Time to stop download
            resolution: Resolution in seconds between tick (ex: 60 = 1 per minute)
        Returns:
            Dataframe with *at least* 'time (epoch)', 'low', 'high', 'open', 'close', 'volume' as columns.
        """

        #change something like BTC-USD to BTC/USD
        if "-" in symbol:
            symbol = symbol.replace("-", "/")

        accepted_grans = [15, 60, 300, 900, 3600, 14400, 86400]

        #ftx accepts the above resolutions plus any multiple of 86400 up to 30 * 86400
        for i in range(2, 31):
            accepted_grans.append(i * 86400)

        if resolution not in accepted_grans:
            utils.info_print("Granularity is not an accepted granularity...rounding to nearest valid value.")
            resolution = accepted_grans[min(range(len(accepted_grans)),
                                            key=lambda i: abs(accepted_grans[i] - resolution))]
        
        history = self.get_calls().get_product_history(symbol, epoch_start, epoch_stop, resolution)
        
        total_num_intervals = len(history)

        total_data = []

        for interval_num, interval in enumerate(history):
            epoch_start = int(utils.epoch_from_ISO8601(interval["startTime"]))
            interval_low = float(interval["low"])
            interval_high = float(interval["high"])
            interval_open = float(interval["open"])
            interval_close = float(interval["close"])
            interval_volume = float(interval["volume"])

            interval_data = [epoch_start, interval_low, interval_high, interval_open, interval_close, interval_volume]
            total_data.append(interval_data)
            
            utils.update_progress(interval_num / total_num_intervals)
        
        df = pandas.DataFrame(data = total_data, columns = ['time', 'low', 'high', 'open', 'close', 'volume'])

        print("\n")
        return df

    
    def get_order_filter(self, symbol: str):
        """
        Find order limits for the exchange
        Args:
            symbol: The asset such as (BTC-USD, or MSFT)

            {
                "name": "BTC/USD", <---needed
                "enabled": true,
                "postOnly": false,
                "priceIncrement": 1.0, <------ needed
                "sizeIncrement": 0.0001, <------ needed
                "minProvideSize": 0.0001, <------ needed
                "last": 47534.0,
                "bid": 47536.0,
                "ask": 47540.0,
                "price": 47536.0,
                "type": "spot",
                "baseCurrency": "BTC", <------ needed
                "quoteCurrency": "USD", <------ needed
                "underlying": null,
                "restricted": false,
                "highLeverageFeeExempt": true,
                "change1h": -0.007184628237259816,
                "change24h": -0.003438155136268344,
                "changeBod": 0.02373260972563208,
                "quoteVolume24h": 57477234.2424,
                "volumeUsd24h": 57477234.2424
            }

        """
        if "-" in symbol:
            symbol = symbol.replace("-", "/")
        

        market_info = self.get_calls().get_market(symbol)

        exchange_specific_keys = copy.deepcopy(market_info)

        keys_to_remove = ["name", "baseCurrency", "quoteCurrency", "minProvideSize", "sizeIncrement", "priceIncrement", "price"]

        for key in keys_to_remove:
            exchange_specific_keys.pop(key)

        return {
            "symbol": market_info["name"],
            "base_asset": market_info["baseCurrency"],
            "quote_asset": market_info["quoteCurrency"],
            "max_orders": 99999999,
            "limit_order": {
                "base_min_size": market_info["minProvideSize"],
                "base_max_size": 99999999,
                "base_increment": market_info["sizeIncrement"],
                "price_increment": market_info["priceIncrement"],
                "min_price": market_info["minProvideSize"] * market_info["price"],
                "max_price": 99999999 * market_info["price"]
            },
            "market_order": {
                "base_min_size": market_info["minProvideSize"],
                "base_max_size": 99999999,
                "base_increment": market_info["sizeIncrement"],
                "quote_increment": market_info["priceIncrement"],
                "buy": {
                    "min_funds": None,
                    "max_funds": None
                },
                "sell": {
                    "min_funds": None,
                    "max_funds": None
                },
                "exchange_specific": exchange_specific_keys
            }
            
        }

    
    def get_price(self, symbol: str) -> float:
        """
        Returns just the price of a symbol.
        Args:
            symbol: The asset such as (BTC-USD, or MSFT)
        """
        return float(self.get_calls().get_market(symbol)['price'])

