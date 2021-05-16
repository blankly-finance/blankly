class Order():
    def __init__(self, order_type, side, size, price=None):
        if order_type not in ['market', 'limit']:
            raise ValueError("Order types can only be of type ['market', 'limit'], but was given: {}".format(order_type))
        self.type = order_type
        if side not in ['buy', 'sell']:
                raise ValueError("Order side can only be of type ['buy', 'sell'], but was given: {}".format(order_type))
        self.side = side
        if self.size <= 0:
            raise ValueError("Size must be greater than zero, but was given: {}".format(size))
        if self.type == 'limit' and price == None:
            raise ValueError("Limit orders require a price but None was given")

        if price <= 0:
            raise ValueError("Price must be greater than zero but was given: {}".format(price))

        self.price = price
        