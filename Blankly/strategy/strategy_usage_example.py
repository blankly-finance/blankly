from Blankly.strategy.order import Order
import Blankly
from Blankly.strategy.strategy_base import Strategy


def golden_cross(price, currency_pair, **kwargs):
    # we give you an assortment of values 
    # as well as access to the underlying strategy or interface
    portfolio_value = kwargs['portfolio_value']
    resolution = kwargs['resolution']

    historical_prices = Blankly.historical(currency_pair, 50, resolution=resolution)
    sma50 = Blankly.analysis.calculate_sma(historical_prices, window=50)[-1] # last 50 day sma value is the value we want
    if price > sma50:
        return Order(currency_pair, 'market', 'buy', portfolio_value * 0.25)
    else:
        return Order(currency_pair, 'market', 'buy', portfolio_value * 0.25)

def rsi(price, currency_pair, **kwargs):
    portfolio_value = kwargs['portfolio_value']
    resolution = kwargs['resolution']
    
    historical_prices = Blankly.historical(currency_pair, 50)
    historical_prices = Blankly.historical(currency_pair, 50, resolution=resolution)
    rsi = Blankly.analysis.calculate_rsi(historical_prices, window=10)[-1] # last 50 day sma value is the value we want
    if rsi < 30:
        return Order(currency_pair, 'market', 'buy', portfolio_value * 0.35)
    elif rsi > 70:
        return Order(currency_pair, 'market', 'buy', portfolio_value * 0.35)


if __name__ == "__main__":
    coinbase_pro = Blankly.Coinbase_Pro()
    coinbase_strategy = Strategy(coinbase_pro)

    coinbase_strategy.add_price_event(golden_cross, currency_pair='BTC-USD', resolution='15m')
    coinbase_strategy.add_price_event(rsi, currency_pair='XLM-USD', resolution='15m')
    coinbase_strategy.add_price_event(golden_cross, currency_pair='COMP-USD', resolution='30m')
    coinbase_strategy.add_price_event(rsi, currency_pair='COMP-USD', resolution='15m')
