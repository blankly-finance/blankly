from blankly import Screener, Alpaca, ScreenerState
from blankly.indicators import rsi

tickers = ['AAPL', 'GME', 'MSFT']  # any stocks that you may want


# This function is our evaluator and runs per stock
def is_stock_buy(symbol, state: ScreenerState):
    # This runs per stock
    prices = state.interface.history(symbol, 40, resolution='1d',
                                     return_as='list')  # get past 40 data points
    price = state.interface.get_price(symbol)
    rsi_values = rsi(prices['close'], 14)
    return {'is_oversold': bool(rsi_values[-1] < 30), 'price': price, 'symbol': symbol}

def formatter(results, state: ScreenerState):
    # results is a dictionary on a per-symbol basis
    result_string = 'These are all the stocks that are currently oversold: \n'
    for symbol in results:
        if results[symbol]['is_oversold']:
            result_string += '{} is currently oversold at a price of {}\n\n'.format(symbol, results[symbol]['price'])
    return result_string


if __name__ == "__main__":
    alpaca = Alpaca()  # initialize our interface
    screener = Screener(alpaca, is_stock_buy, symbols=tickers, formatter=formatter)  # find oversold

    print(screener.formatted_results)
