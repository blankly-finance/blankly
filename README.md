![Blankly_Written_Logo_White](./Images/Blankly_Logo_White.svg)
![Blankly_Written_Logo_White](./Images/Blankly_Written_Logo_Github_Dark.svg)

## What is it?

​	Blankly is an elegant python library for interacting with many different crypto exchanges in a consistent way. You might say "I've already seen this before" but I really doubt you have. Look at these examples for buying on different exchanges:

### Coinbase Pro:

```python
self.Interface.market_order(.01, "buy", "BTC-USD")
```

## Current Market Commands Support

| **Command**     | Arguments                      | Description                                                  | Coinbase Pro |
| --------------- | ------------------------------ | ------------------------------------------------------------ | ------------ |
| **Market Buy**  | `amount, "buy", "Coin-ID"`     | Creates a market buy of the specified currency of the specified amount | ✅            |
| **Market Sell** | `amount, "sell", "Coin-ID"`    | Creates a market sell of the specified currency of the specified amount | ✅            |
| **Limit Buy**   | `size, price, "buy", Coin-ID`  | Creates a limit buy of the specified currency at the specified price and amount | ✅            |
| **Limit Sell**  | `size, price, "sell", Coin-ID` | Creates a limit sell of the specified currency at the specified price and amount | ✅            |

## Ticker Support

| Exchange         | Type      | Default Callback    |
| ---------------- | --------- | ------------------- |
| **Coinbase Pro** | Websocket | `price_event(tick)` |

### Declaration

```python
self.Interface.create_ticker(self, Coin_ID)
```

When created in a class, this will callback the `price_event(tick)` function.

## Multiprocessing Feature
Blankly is designed to allow running models independently, each on their own process. This allows the ability to run intensive tasks, such as training a neural network independently of all the other models, causing no lag to the main process.

## Bugs

Please report any bugs or issues in Github's Issues page

## Contributing

If you would like to support the project, pull requests are welcome.