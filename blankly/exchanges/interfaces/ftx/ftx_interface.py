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
        print("delete this print statement")
        pass
        
    def get_calls(self):
        """
        Get the direct & authenticated exchange object

        Returns:
             The exchange's direct calls object. A blankly Bot class should have immediate access to this by
             default
        """
        return self.calls

    
    def get_exchange_type(self):
        """
        Get the type of exchange ex: "coinbase_pro" or "binance"

        Returns:
             A string that corresponds to the type of exchange

        TODO add return example
        """
        pass

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

    
    def get_account(self,
                    symbol: str = None) -> utils.AttributeDict:
        """
        Get all assets in an account, or sort by symbol/account_id
        Args:
            symbol (Optional): Filter by particular symbol

            These arguments are mutually exclusive

        TODO add return example
        """
        pass

    
    def market_order(self,
                     symbol: str,
                     side: str,
                     size: float) -> MarketOrder:
        """
        Used for buying or selling market orders
        Args:
            symbol: asset to buy
            side: buy/sell
            size: desired amount of base asset to use
        """
        pass

    
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
        pass

    
    def cancel_order(self,
                     symbol: str,
                     order_id: str) -> dict:
        """
        Cancel an order on a particular symbol & order id

        Args:
            symbol: This is the asset id that the order is under
            order_id: The unique ID of the order.

        TODO add return example
        """

    
    def get_open_orders(self,
                        symbol: str = None) -> list:
        """
        List open orders.
        Args:
            symbol (optional) (str): Asset such as BTC-USD
        TODO add return example
        """
        pass

    
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

