import Blankly
from Blankly.strategy.strategy_base import Strategy

prices = []


def price_event(price, currency_pair):
    prices.append(price)
    sma50 = Blankly.indicators.sma(price, 10)
    if price > sma50:
        interface.market_order(currency_pair, 'buy', 10)
    else:
        interface.market_order(currency_pair, 'sell', 10)


if __name__ == "__main__":
    # Authenticate coinbase pro strategy
    coinbase_pro = Blankly.Coinbase_Pro()
    interface = coinbase_pro.get_interface()
    coinbase_strategy = Strategy(coinbase_pro)

    coinbase_strategy.add_price_event(price_event, currency_pair='BTC-USD', resolution='15m')
    coinbase_strategy.add_price_event(price_event, currency_pair='XLM-USD', resolution='15m')
    coinbase_strategy.add_price_event(price_event, currency_pair='COMP-USD', resolution='15m')
