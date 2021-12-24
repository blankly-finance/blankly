import pandas
from blankly.exchanges.interfaces.exchange_interface import ExchangeInterface
from blankly.exchanges.orders.market_order import MarketOrder
from blankly.exchanges.orders.limit_order import LimitOrder
import blankly.utils.utils as utils
#
class FTXInterface(ExchangeInterface):
        
    def __init__(self, exchange_name, authenticated_API):
        super().__init__(exchange_name, authenticated_API, valid_resolutions=None)

    def get_calls(self):
        """
        Get the direct & authenticated exchange object

        Returns:
             The exchange's direct calls object. A blankly Bot class should have immediate access to this by
             default
        """
        pass

    
    def get_exchange_type(self):
        """
        Get the type of exchange ex: "coinbase_pro" or "binance"

        Returns:
             A string that corresponds to the type of exchange

        TODO add return example
        """
        pass

    
    def get_products(self) -> list:
        """
        Get all trading pairs on the exchange & some information about the exchange limits.

        TODO add return example
        """
        pass

    
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

