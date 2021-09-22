

<br />

<div align="center">
   <img style="margin: 0 auto; padding-bottom: 15px; padding-top: 30px" width=70%" src="https://firebasestorage.googleapis.com/v0/b/blankly-6ada5.appspot.com/o/blankly-github-logo.png?alt=media&token=8f436cd2-3d28-432c-867a-afef780f4260">
</div>
<br />
<div align="center">
  <b>💨  Rapidly build and deploy quantitative models for stocks, crypto, and forex  🚀</b>
</div>
<br />

<p align="center">
   <a target="_blank" href="https://sonarcloud.io/dashboard?id=Blankly-Finance_Blankly"><img src="https://sonarcloud.io/api/project_badges/measure?project=Blankly-Finance_Blankly&metric=sqale_rating"></a>
   <a target="_blank" href="https://sonarcloud.io/dashboard?id=Blankly-Finance_Blankly"><img src="https://sonarcloud.io/api/project_badges/measure?project=Blankly-Finance_Blankly&metric=security_rating"></a>
   <a target="_blank" href="https://sonarcloud.io/dashboard?id=Blankly-Finance_Blankly"><img src="https://sonarcloud.io/api/project_badges/measure?project=Blankly-Finance_Blankly&metric=alert_status"></a>
   <a target="_blank" href="https://github.com/Blankly-Finance/Blankly/actions/workflows/test.yml"><img src="https://github.com/Blankly-Finance/Blankly/actions/workflows/test.yml/badge.svg?branch=main"></a> <br>
   <a target="_blank" href="https://pepy.tech/project/blankly"><img src="https://pepy.tech/badge/blankly/month"></a>
   <a target="_blank" href="https://github.com/Blankly-Finance/Blankly/blob/main/LICENSE"><img src="https://img.shields.io/pypi/l/blankly?color=gree"></a>
   <a target="_blank" href="https://github.com/Blankly-Finance/Blankly/stargazers"><img src="https://img.shields.io/github/stars/blankly-finance/blankly?style=social"></a>
   
   

</p>
<p align="center">
    <a target="_blank" href="https://docs.blankly.finance">View Docs</a>
    ·
    <a href="https://blankly.finance">Our Website</a>
    ·
    <a href="#quickstart">Getting Started</a>
  </p>

---

## Why Blankly? 

Blankly is an elegant python library for interacting with crypto, stocks, and forex for in a consistent and streamlined way. Now, no more reading API or struggling to get data. Blankly offers a powerful feature-set, optimized for speed and ease of use, better backtesting, and ultimately better models. 

We're bridging the gap between local development systems & live APIs by building a framework which allows backtesting, 
paper trading, sandbox testing, and live cross-exchange deployment without modifying a single line of trading logic.

Check out our [website](https://blankly.finance) and our [docs](https://docs.blankly.finance).

### Trade Stocks, Crypto, and Forex Seamlessly

```python
from blankly import Alpaca, CoinbasePro

stocks = Alpaca()
crypto = CoinbasePro()

# Easily perform the same actions across exchanges & asset types
stocks.interface.market_order('AAPL', 'buy', 10)
crypto.interface.market_order('BTC-USD', 'buy', 10)
```

### Backtest Instantly Across Symbols

```python
from blankly import Alpaca, Strategy, StrategyState

def price_event(price, symbol, state):
	# Trading logic here
  state.interface.market_order(symbol, 'buy', 10)
  
# Authenticate
alpaca = Alpaca()
strategy = Strategy(alpaca)

# Check price every hour and send to the strategy function
# Easily switch resolutions and data
strategy.add_price_event(price_event, 'AAPL', '1h')
strategy.add_price_event(price_event, 'MSFT', '15m')

# Run the backtest
strategy.backtest(to='1y')
```

#### Accurate Backtest Holdings

<div align="center">
  <img style="margin: 0 auto; padding-bottom: 15px; padding-top: 30px" width=100%" src="https://firebasestorage.googleapis.com/v0/b/blankly-6ada5.appspot.com/o/screely-1631725027541.png?alt=media&token=1446fcf0-680b-4ee9-afcf-fbaea044eba7">
</div>

#### Useful Metrics

```bash
cagr: 0.16389971631401057
cum_returns: 0.16341583811462995
sortino: 0.9357010686544994
sharpe: 0.9194457112821073
calmar: 1.103453797087196e-05
volatility: 0.7740509744474758
variance: 0.5991549110430868
var: 156.2040441889991
cvar: 6.508901021574862
```
### Go Live in One Line

Seamlessly run your model live!

```python
# Just turn this
strategy.backtest(to='1y')
# Into this
strategy.start()
```

Dates, times, and scheduling adjust on the backend to make the experience instant.

## Quickstart

### Installation

1. First install Blankly using `pip`. Blankly is hosted on [PyPi](https://pypi.org/project/Blankly/).

```bash
$ pip install blankly
```

2. Next, just run:
```bash
$ blankly init
```
This will initialize your working directory.

The command will create the files `keys.json`, `settings.json`, `backtest.json`, `deploy.json` and an example script called `bot.py`.

If you don't want to use our `init` command, you can find the same files in the `examples` folder under [`settings.json`](https://github.com/Blankly-Finance/Blankly/blob/main/examples/settings.json) and [`keys_example.json`](https://github.com/Blankly-Finance/Blankly/blob/main/examples/keys_example.json)

3. From there, **insert your API keys** from your exchange into the generated `keys.json` file.

More information can be found on our [docs](https://docs.blankly.finance)

### Directory format

The working directory format should have at least these files:
```
Project
   |-bot.py
   |-keys.json
   |-settings.json
```

#### Additional Info

Make sure you're using a supported version of python. The module is currently tested on these versions:

- Python 3.7+

For more info, and ways to do more advanced things, check out our [getting started docs](https://docs.blankly.finance).

## Supported Exchanges

| Exchange     | REST Support | Ticker Websocket | Order Book | Interface |
| ------------ | ------------ | ---------------- | ---------- | --------- |
| Coinbase Pro | 🟢           | 🟢               | 🟢        | 🟢        |
| Binance      | 🟢           | 🟢               | 🟢        | 🟢       |
| Alpaca       | 🟢         | 🟢             | 🟢      | 🟢        |
| OANDA | 🟡 | 🟡 | 🟡 | 🟡 |

🟢  = working

🟡  = in development, some or most features are working

🔴  = planned but not yet in development

* Interface calls take ~300 µs extra to homogenize the exchange data.

## RSI Example

We have a pre-built cookbook examples that implement strategies such as RSI, MACD, and the Golden Cross found in our [examples](https://docs.blankly.finance/examples/golden-cross).

The model below will run an RSI check every 30 minutes - **buying** below **30** and **selling** above **70** .

```python
import blankly
from blankly import StrategyState


def price_event(price, symbol, state: StrategyState):
    """ This function will give an updated price every 15 seconds from our definition below """
    state.variables['history'].append(price)
    rsi = blankly.indicators.rsi(state.variables['history'])
    if rsi[-1] < 30 and not state.variables['has_bought']:
        # Dollar cost average buy
        state.variables['has_bought'] = True
        state.interface.market_order(symbol, side='buy', funds=10)
    elif rsi[-1] > 70 and state.variables['has_bought']:
        # Dollar cost average sell
        state.variables['has_bought'] = False
        state.interface.market_order(symbol, side='sell', funds=10)


def init(symbol, state: StrategyState):
    # Download price data to give context to the algo
    state.variables['history'] = state.interface.history(symbol, to='1y', return_as='list')['open']
    state.variables['has_bought'] = False


if __name__ == "__main__":
    # Authenticate coinbase pro strategy
    alpaca = blankly.Alpaca()

    # Use our strategy helper on coinbase pro
    strategy = blankly.Strategy(alpaca)

    # Run the price event function every time we check for a new price - by default that is 15 seconds
    strategy.add_price_event(price_event, symbol='NCLH', resolution='30m', init=init)
    strategy.add_price_event(price_event, symbol='CRBP', resolution='1h', init=init)
    strategy.add_price_event(price_event, symbol='D', resolution='15m', init=init)
    strategy.add_price_event(price_event, symbol='GME', resolution='30m', init=init)

    # Start the strategy. This will begin each of the price event ticks
    # coinbase_strategy.start()
    # Or backtest using this
    strategy.backtest(to='1y')
```
## Other Info

### Bugs

Please report any bugs or issues on the GitHub's Issues page.

### Disclaimer 

Trading is risky. We are not responsible for losses incurred using this software, software fitness for any particular purpose, or responsibility for any issues or bugs.
This is free software.

### Contributing

If you would like to support the project, pull requests are welcome.
You can also contribute just by telling us what you think of Blankly: https://forms.gle/4oAjG9MKRTYKX2hP9

### Licensing 

**Blankly** is distributed under the [**LGPL License**](https://www.gnu.org/licenses/lgpl-3.0.en.html). See the [LICENSE](/LICENSE) for more details.

New updates every day 💪.
