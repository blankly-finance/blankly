# Backtesting Engine

The blankly backtesting engine is designed for accurate & realistic evaluation of historical trades in the **spot, futures, stocks and forex** markets. While requiring minimal configuration out of the box to achieve highly accurate results.

## Design Considerations

### Order Filter

All trades are evaluated against the order filter required by the exchange. This removes a large degree of uncertainty when moving to live trading by preventing a strategy that relies on impossible trades during development phase.

The backtester evaluates these filter metrics:

- Limit order minimum size
- Limit order maximum size
- Base size increment
- Price increment for limit orders
- Max/min price for limit orders
- If the asset is fractional
- Notional differences between the buy/sell side
- Percentage price for limit orders (i.e Binance +- 25% filter)

### Exchange Data

Blankly pulls & caches data directly from the user's exchange. Per-exchange data is important because prices can vary significantly between different exchanges depending on asset type.

### Custom Events - Tweets, Websockets or Simulated Latency

The backtesting engine exposes the ability to create event-driven strategies. By providing the backtesting engine with a set of events (prices or sentiment data), these events can be correctly evaluated as a valid trading strategy.

```python
    # New events are injected here
    def event(self, type_: str, data: str):
        # Now check if it's a tweet about microsoft
        if type_ == "tweet":
            if 'msft' in data.lower():
                print("Buying microsoft...")
                self.interface.market_order('MSFT', 'buy', 1)
            else:
                print("Message did not contain microsoft")
```

A latency sensitive strategy can also be tested in this framework by using `self.sleep(seconds)`.

### Short Selling & Margin

Blankly accurate evaluates short positions on Alpaca. This includes accurate margin calculations by continually evaluating buying power against Alpaca's margin rules. This short selling capability can be extended to other exchanges for those interested in experimenting.

### Fees

Fees are downloaded from the user's exchange directly, following the user's pricing tier. For example, if the user has traded `100k<1M` on Coinbase Pro, the fees will be correctly set to `0.20%` taker and `0.10%` maker. This is important because high-volume users have access to lower exchange rates.

### Limit Orders

During backtesting, all limit orders are evaluated every time the price changes. The engine does not take into account changes in price that occur at a higher resolution than the downloaded data (for example a limit buy @ `$1000` will not execute if the price dips to `$999` ).

## Speed (event based vs vectorization)

Blankly uses an event-based approach rather than a vectorized approach to evaluate backtests. This is a slower but much more realistic way to evaluate model performance. When compared to other event-based engines such as Jesse AI, our engine is significantly faster. The engine is able to run the backtest event loop extremely quickly. This means blankly can run year long backtest in less than 3 seconds when compared to 5+ minutes with Jesse AI.

## Market Hours

Blankly accurately evaluates market open & market closes. Just like how Alpaca behaves when live, orders can be submitted in a pending status and execute extremely close to the open price. This behavior will be expanded as we add more traditional equity exchanges.

## Futures Trading

Blankly has begun the process of integrating one of the first open source futures backtesting engine available. The engine is still in beta but is currently correctly evaluating buy/sells against the price. Downloading & caching funding rates is currently in development.

## Suggested Features

- Slippage Models
  - The current backtesting engine assumes infinite resting liquidity, meaning orders fill at the exact current price. For high volume or high frequency traders this can often be inaccurate.
  - By evaluating the existing liquidity using an orderbook or taking advantage of a **community maintained database**, accurate slippage models could be created per exchange and per asset.
