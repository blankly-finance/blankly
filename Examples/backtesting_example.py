from Blankly.utils.utils import AttributeDict
from Blankly.strategy.strategy_state import StrategyState
import Blankly
from Blankly.strategy import Strategy, StrategyStatee


def golden_cross(price, currency_pair, interface: Blankly.Interface, state: StrategyState):
    resolution: str = state.resolution # get the resolution that this price event is stored at
    variables = state.variables # each price event has it's own local variable state

    account = interface.account # get account holdings

    historical_prices = Blankly.historical(currency_pair, 50, resolution=resolution)
    sma50 = Blankly.analysis.calculate_sma(historical_prices, window=50)[-1] # last 50 day sma value is the value we want

    if price > sma50 and variables['order_submitted']:
        variables['order_submitted'] = True
        interface.market_order(currency_pair, 'buy', account.cash * 0.25)
    elif price < sma50: # only sell if there's an open position
        variables['order_submitted'] = False
        stocks_available = account.holdings[currency_pair].available * 0.5 # sell 50% of available sures
        interface.market_order(currency_pair, 'sell', stocks_available)


if __name__ == "__main__":
    """
    Authenticate
    """
    print("Authenticating...")
    # Create an authenticated coinbase pro object
    coinbase_pro = Blankly.Coinbase_Pro()

    # Create a strategy object
    strategy = Blankly.Strategy(coinbase_pro)

    """
    Backtest
    """
    print("Backtesting...")
    # Add the function to the strategy class
    strategy.add_price_event(golden_cross, 'BTC-USD', resolution='1h')
    strategy.add_price_event(golden_cross, 'BTC-USD', resolution='15m')

    # The backtest function will now turn our strategy class into a class that can be backtested
    print(strategy.backtest(to='10d'))
