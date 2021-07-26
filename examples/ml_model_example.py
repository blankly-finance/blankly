from blankly import Strategy, StrategyState, Interface
from blankly import Alpaca
from blankly.indicators import rsi, sma
from sklearn.neural_network import MLPClassifier
from sklearn.datasets import make_classification
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split

def init(symbol, state: StrategyState):
    interface: Interface = state.interface
    resolution: str = state.resolution
    variables = state.variables
    X, y = make_classification(n_samples=500, n_features=3, n_informative=3, n_redundant=0, random_state=1)
    X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, random_state=1)
    # initialize the historical data
    variables['model'] = MLPClassifier(random_state=1, max_iter=300).fit(X_train, y_train)
    variables['history'] = interface.history(symbol, 300, resolution)['close']
    variables['has_bought'] = False

def price_event(price, symbol, state: StrategyState):
    interface: Interface = state.interface
    variables = state.variables

    variables['history'].append(price)
    model = variables['model']
    scaler = MinMaxScaler()
    rsi_values = rsi(variables['history'], period=14)
    rsi_value = scaler.fit_transform(rsi_values)[-1]

    ma_values = sma(variables['history'], period=50)
    ma_value = scaler.fit_transform(ma_values)[-1]

    ma100_values = sma(variables['history'], period=100)
    ma100_value = scaler.fit_transform(ma100_values)[-1]

    prediction = model.predict([rsi_value, ma_value, ma100_value])
    # comparing prev diff with current diff will show a cross
    if prediction == 1:
        interface.market_order('buy', symbol, interface.cash)
        variables['has_bought'] = True
    elif prediction == 0 and variables['has_bought']:
        curr_value = interface.account[symbol].available * price
        interface.market_order('sell', symbol, curr_value)
        variables['has_bought'] = False

alpaca = Alpaca()
s = Strategy(alpaca)
# creating an init allows us to run the same function for 
# different tickers and resolutions
s.add_price_event(price_event, 'MSFT', resolution='15m', init=init)
s.add_price_event(price_event, 'AAPL', resolution='1d', init=init)
s.backtest(initial_values={'USD': 10000}, to='2y')