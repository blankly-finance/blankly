import pandas
from blankly.exchanges.interfaces.exchange_interface import ExchangeInterface
from blankly.exchanges.orders.market_order import MarketOrder
from blankly.exchanges.orders.limit_order import LimitOrder
from blankly.exchanges.interfaces.ftx.ftx_api import FTXAPI
import blankly.utils.utils as utils
import json
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
                product['base_max_size'] = None
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

    
    def get_open_orders(self,
                        symbol: str = None) -> list:
        """
        List open orders.
        Args:
            symbol (optional) (str): Asset such as BTC-USD
        """
        

    
    def get_order(self,
                  symbol: str,
                  order_id: str) -> dict:
        """
        Get a certain order
        Args:
            symbol: Asset that the order is under
            order_id: The unique ID of the order.
        TODO add return example
        """
        pass

    
    def get_fees(self) -> dict:
        """
        Get market fees
        TODO add return example
        """
        pass

    
    def get_product_history(self,
                            symbol: str,
                            epoch_start: float,
                            epoch_stop: float,
                            resolution) -> pandas.DataFrame:
        """
        Returns the product history from an exchange
        Args:
            symbol: The asset such as (BTC-USD, or MSFT)
            epoch_start: Time to begin download
            epoch_stop: Time to stop download
            resolution: Resolution in seconds between tick (ex: 60 = 1 per minute)
        Returns:
            Dataframe with *at least* 'time (epoch)', 'low', 'high', 'open', 'close', 'volume' as columns.
            TODO add return example
        """

    
    def get_order_filter(self,
                         symbol: str):
        """
        Find order limits for the exchange
        Args:
            symbol: The asset such as (BTC-USD, or MSFT)
            TODO add return example
        """
        pass

    
    def get_price(self, symbol: str) -> float:
        """
        Returns just the price of a symbol.
        Args:
            symbol: The asset such as (BTC-USD, or MSFT)
            TODO add return example
        """
        pass

