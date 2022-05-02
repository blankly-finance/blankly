# Risk On or Risk Off Leveraged S&P 500
from blankly import Alpaca, Strategy, StrategyState
from blankly.metrics import cum_returns
from blankly import trunc


def compare_price_event(prices, symbols, state: StrategyState):
    """ Strategy: When the market is doing well, the strategy takes on more risk by holding a leveraged S&P 500 ETF.
                    When the market is shaky, it folds into treasury bonds."""
    # keep track of history (close price) of all four tickers:
    # - 'BND' (Vanguard Total Bond Market Index Fund ETF)
    # - 'BIL' (SPDR Bloomberg 1-3 Month T-Bill ETF)
    # - 'UPRO' (ProShares UltraPro S&P500)
    # - 'IEF' (iShares 7-10 Year Treasury Bond ETF)
    for symbol in symbols:
        history_name = str(symbol) + '_history'
        state.variables[history_name].append(prices[symbol])

    # If we don't have enough data to make any decisions, pass
    if len(state.variables['BND_history']) < 60:
        return

    # Calculate the 60d cumulative sum of BND and BIL
    state.variables['cum_return_BND_60'] = cum_returns(state.variables['BND_history'][-60],
                                                       state.variables['BND_history'][-1])
    state.variables['cum_return_BIL_60'] = cum_returns(state.variables['BIL_history'][-60],
                                                       state.variables['BIL_history'][-1])

    # If 60d cumulative return of BND is greater than 60d cumulative return of BIL -> market is doing well
    if state.variables['cum_return_BND_60'] > state.variables['cum_return_BIL_60']:
        # Sell all of the IEF shares that we have
        curr_value_IEF = trunc(state.interface.account['IEF'].available, 2)
        if curr_value_IEF > 0:
            state.interface.market_order(symbol='IEF', side='sell', size=curr_value_IEF)

        # Buy the UPRO shares if we have any cash left
        price = state.variables['UPRO_history'][-1]
        size = trunc(state.interface.cash / price, 2)
        if size > 0:
            state.interface.market_order(symbol='UPRO', side='buy', size=size)
    else:
        # Sell all of the UPRO shares that we have
        curr_value_UPRO = trunc(state.interface.account['UPRO'].available, 2)
        if curr_value_UPRO > 0:
            state.interface.market_order(symbol='UPRO', side='sell', size=curr_value_UPRO)
        # Buy the IEF shares if we have any cash left (treasury bond)
        price = state.variables['IEF_history'][-1]
        size = trunc(state.interface.cash / price, 2)
        if size > 0:
            state.interface.market_order(symbol='IEF', side='buy', size=size)


def init(symbols, state: StrategyState):
    # Download price data of the four tickers: 'BND', 'BIL', 'UPRO', 'IEF'
    for symbol in symbols:
        history_name = str(symbol) + '_history'
        state.variables[history_name] = state.interface.history(symbol, to=150, return_as='deque',
                                                                resolution=state.resolution)['close']
    # Initialize the variables needed for the compare_price_event
    state.variables['cum_return_BND_60'] = 0
    state.variables['cum_return_BIL_60'] = 0


if __name__ == "__main__":
    # Authenticate Alpaca strategy
    exchange = Alpaca(portfolio_name="epic portfolio")

    # Use our strategy helper on Alpaca
    strategy = Strategy(exchange)

    # Run the compare price event function every time we check for a new price - by default that is 15 seconds
    strategy.add_arbitrage_event(compare_price_event, ['BND', 'BIL', 'UPRO', 'IEF'], resolution='1d', init=init)

    # Start the strategy. This will begin each of the price event ticks
    # strategy.start()
    # Or backtest using this
    results = strategy.backtest(to='2y', initial_values={'USD': 10000})
    print(results)
