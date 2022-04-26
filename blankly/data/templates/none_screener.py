from blankly import Screener, ScreenerState


def evaluator(symbol, state: ScreenerState):
    pass


def formatter(results, state: ScreenerState):
    pass


if __name__ == '__main__':
    exchange = EXCHANGE_CLASS()  # initialize our exchange
    screener = Screener(exchange, evaluator, symbols=[], formatter=formatter)  # find oversold

    print(screener.formatted_results)
