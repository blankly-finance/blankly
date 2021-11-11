"""
    This shows how you can easily wrap in your own logic. Pull in your own scripts to make them backtestable and make
    them run live
"""

from blankly import Strategy, StrategyState, Interface
from blankly import Alpaca

# Example import (these imports will fail they just show how you might call a module)
from models import OrderPricingModel, OrderDecisionModel


def init(symbol, state: StrategyState):
    # initialize this once and store it into state
    variables = state.variables
    variables['decision_model'] = OrderDecisionModel(symbol)
    variables['pricing_model'] = OrderPricingModel(symbol)
    variables['has_bought'] = False


def price_event(price, symbol, state: StrategyState):
    interface: Interface = state.interface
    variables = state.variables
    decision_model = variables['decision_model']
    pricing_model = variables['pricing_model']

    # make a decision to buy, sell, or hold
    decision = decision_model(symbol)

    if decision == 0:
        curr_value = interface.account[symbol].available * price
        # call pricing model to determine how much to buy
        amt_to_buy = pricing_model(price, symbol, interface.cash, curr_value)
        interface.market_order(symbol, 'buy', amt_to_buy)
    elif decision == 1:
        curr_value = interface.account[symbol].available * price
        amt_to_sell = pricing_model(price, symbol, interface.cash, curr_value)
        interface.market_order(symbol, 'sell', amt_to_sell)


if __name__ == "__main__":
    alpaca = Alpaca()
    s = Strategy(alpaca)
    s.add_price_event(price_event, 'MSFT', resolution='1d', init=init)
    # decision_model = OrderDecisionModel() <-- global state can also be accessed in price event functions
    # pricing_model = OrderPricingModel()
    s.backtest(initial_values={'USD': 10000}, to='2y')

