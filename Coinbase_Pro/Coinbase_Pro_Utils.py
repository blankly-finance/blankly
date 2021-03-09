class CoinbaseProUtils:
    def __init__(self):
        pass


    """
    Size: Amount of base currency to buy or sell
    Price: Price per bitcoin
    Ex: Buy .001BTC at $15,000 is generateLimitOrder(.001, 15000, "buy", "BTC-USD")
    """
    """
    Order Place Example:
    order = {
        'size': 1.0,
        'price': 1.0,
        'side': 'buy',
        'product_id': 'BTC-USD',
    }
    (size in currency (like .01 BTC), buy/sell (string), product id (BTC-USD))
    """
    def generate_limit_order(self, size, price, side, product_id):
        order = {
            'size': size,
            'price': price,
            'side': side,
            'product_id': product_id,
        }
        return order

    """
    Size: Amount of base currency to buy or sell
    (size in currency (like .01 BTC), buy/sell (string), product id (BTC-USD))
    """
    def generate_market_order(self, size, side, product_id):
        order = {
            'size': size,
            'side': side,
            'product_id': product_id,
        }
        return order