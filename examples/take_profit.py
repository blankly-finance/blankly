import blankly
from blankly import Side


def price_event(price, symbol, state: blankly.StrategyState):
    order = state.variables.get('order', None)

    if order is None:
        market = state.interface.market_order(symbol, Side.BUY, state.interface.cash / price)
        order_size = state.interface.get_account(symbol)['available']

        # place a take-profit order at 20% above the current price
        stop_loss = state.interface.take_profit_order(symbol, price * 1.2, order_size)

        state.variables['order'] = stop_loss.get_id()
        return

    order_status = state.interface.get_order(symbol, state.variables['order'])['status']
    if order_status in ('done', 'filled'):
        # our take-profit order was executed
        pass


if __name__ == "__main__":
    # Authenticate coinbase pro strategy
    exchange = blankly.CoinbasePro()

    # Use our strategy helper on coinbase pro
    strategy = blankly.Strategy(exchange)

    # Run the price event function every time we check for a new price - by default that is 15 seconds
    strategy.add_price_event(price_event, symbol='ETH-USD', resolution='1d')

    if blankly.is_deployed:
        strategy.start()
    else:
        strategy.backtest(to='1y', initial_values={'USD': 10000})
