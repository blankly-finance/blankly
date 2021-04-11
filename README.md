![Blankly_Github_Logo](./Images/Blankly_Github_Logo.svg)

## What is it?

​	Blankly is an elegant python library for interacting with many different crypto exchanges on multiple portfolios in a consistent way. Blankly offers a powerful feature-set, optimized for speed and ease of use.



Check out our [website](http://blankly.net).

## Features

- Full REST API support for non-margin accounts on listed exchanges

- Ticker websocket support

- Order book websocket support **

- Fully multiprocessed bots with flexible arguments.

- Quickstart access for interacting with exchanges

- Support for multiple portfolios on multiple exchanges, all independently

- Multi-process communication

- Profit management **

- Long term and high resolution historical data downloads as pandas dataframes

- Single pip module (`pip install Blankly`)

- Asynchronous callbacks from ticker feeds

- ZeroRPC server to report to Javascript or React **

- Easy access to raw API calls

- Customizable circular buffer websocket feeds

- Interface that allows calls to each supported exchange to be identical:

  > Buy example for Coinbase Pro and Binance:
  >
  > Coinbase Pro:
  >
  > ```python
  > self.Interface.market_order(.01, "buy", "BTC-USD")
  > ```
  >
  > Binance: **
  >
  > ```python
  > self.Interface.market_order(.01, "buy", "BTC-USD")
  > ```

** Means that the feature is still in development but has some degree of support.

## Coming Features

- Paper trading system
- Backtesting (`bot.backtest(time_frame)`)
- Deployment (`> Blankly push bot/*`)
- Online GUI and hosting
- C++ acceleration for technical analysis
- Bot can request to authenticate on other user-added exchanges and portfolios

# Quick Start

1. Using Blankly is incredibly easy. It just requires the pip module and 3 basic files. First **install the pip module** by

> `pip install Blankly`

2. Next **you need the files** in the `Examples` folder:

> Basic_Bot.py
>
> Keys_Example.json
>
> Settings.json

3. **Place** these in the `root` or `working directory` of the project.

4. **Rename** `Keys_Example.json` to `Keys.json` or create your own `.json` that has the same structure.

5. **Insert the API keys** from your exchange into the renamed `Keys.json` file.

   1. **You can add multiple portfolios**! You can specify the name of the portfolio to load when you construct the exchange.
   2. Example: `Blankly.Coinbase_Pro(portfolio_name="my cool portfolio")`). 
   3. If you don't provide one to the constructor, it will just default to the first one given in the `Keys.json` file and show a warning.

6. **The script defaults to Coinbase Pro**. If you're using that, great! If not, change the line that says:

   > `exchange = Blankly.Coinbase_Pro()`
   >
   > to one that matches your exchange, such as:
   >
   > `exchange = Blankly.Binance()`

7. **Everything should work**! Run the `Basic_Bot` example in `Basic_Bot.py`. Note a warning will be shown because the `Basic_Bot` script does not specify the exchange name by default (explained in step 5 above).
    - Note the library is developed on Python 3.7, but most modern versions of python 3 should work.

## What is it doing?

The comments offer a decent amount of description for the behavior, but here is a broader overview:

​	The motivation behind this is to **allow full independence** between each bot, but still **giving it the ability to report** back to the main thread easily. The setup runs by specifying three increasingly specific things about the behavior we want:

1. We first **declare** that we want to run on a certain `exchange`, such as Coinbase Pro or Binance. This is done with (for example) `Blankly.Coinbase_Pro()`

   - Documentation refers to this as the `exchange`

   - ```python
     if __name__ == "__main__":
         """
         Easily setup and run a model on any exchange
         """
     
         # This creates an authenticated exchange. Now we can append models.
         exchange = Blankly.Coinbase_Pro()
         # Imagine this:
         #   Coinbase Pro <-- Choosing to assign this bot to this exchange
         #   Kraken
         #   Binance
     ```

2. We initialize the bot object. This creates a boilerplate bot that isn't attached or running on anything yet.

   - ```python
     # Create the bot.
     bot=Bot()
     ```

3. This same function is also **attached** to a `portfolio` within the exchange. Each portfolio has access to each `currency` on the `exchange`. This means that each portfolio is independent from the other. **You can tell it which portfolio you want** by naming it in the `Keys.json` file and then declaring the `portfolio_name` argument to match the same name in `Keys.json`

   - Documentation refers to this set of currencies as a `portfolio`

   - ```python
     # Add it to run as the coinbase_pro bitcoin model
     exchange.append_model(bot, "BTC")
     # Imagine this:
     #   Coinbase Pro:
     #       Bitcoin
     #       Ethereum
     #       Stellar
     #       The Graph <-- Added to the data from this currency
     ```

4. The code above also **declares** the `currency` that we want it to run on within the `portfolio`. The bot is attached to this currency and is provided default ways to interact with the exchange.

   - Documentation calls this the `currency`. Bots are by default **not** currency specific because this dramatically enhances portability.

5. We then ask the model to start. By default this iterates through all the attached models and queries them to start but you can also specify a particular currency to begin executing the bot attached to it.

   - ```python
     # Begins running the main() function of the model on a different process
     exchange.start_models()
     # Imagine this:
     #   Coinbase Pro:
     #       Bitcoin
     #       Ethereum
     #       Stellar
     #       The Graph <-- Bot <-- Asking to start
     ```

6. The bot then starts the main class. The example updates the "heartbeat" value every second. The main thread then reads this and prints it along with some exchange information about that currency.

   - Some default, pre-authenticaed objects are provided to quick start interact with the exchange:

     > self.Interface: allows API through the Blankly exchange interface. The interface object is already authenticated, so the calls are ready to go!

     > self.Ticker_Manager: Allows easy access to a websocket ticker. The actual ticker object can be pulled by self.Ticker_Manager.get_ticker(). This offers all kinds of functionality. See the docs for more information. By default this will be calling the `price_event` function.

   - Main thread calling:

   - ```python
     # Now other processes can be created or just continue with this one.
     while True:
        # Print the state every 2 seconds
        state = exchange.get_full_state("GRT")
        Blankly.Utils.pretty_print_JSON(state)
        time.sleep(1)
     ```

   - Bot state updates:

   - ```python
     while True:
        # This demonstrates a way to change the state. The default script just reports the state on this currency.
        # Increment heartbeat value by one every second
        self.update_state("Heartbeat", self.get_state()["Heartbeat"] + 1)
        time.sleep(1)
     ```

     

# Commands & Docs Overview

## Exchanges

| Exchange     | REST Support | Ticker Websocket | Order Book | Interface |
| ------------ | ------------ | ---------------- | ---------- | --------- |
| Coinbase Pro | 🟢            | 🟢                | 🟢          | 🟢         |
| Binance      | 🟡            | 🟡                | 🔴          | 🟡         |
| Kraken       | 🔴            | 🔴                | 🔴          | 🔴         |

🟢 = full and working

🟡 = in development, some features are working

🔴 = planned but not yet in development

* Interface calls take ~300 microseconds extra to homogenize the exchange data.



## A start on the command documentation:

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
Blankly is designed to allow running models independently, each on their own process. This allows the ability to run intensive tasks, such as training a neural network independently of all the other models on different processor cores, while being able to report and read status from each process.

## Bugs

Please report any bugs or issues in Github's Issues page.

## Disclaimer 

Trading is risky. We are not responsible for losses incurred using this software.

## Contributing

If you would like to support the project, pull requests are welcome.
You can also contribute just by telling us what you think of Blankly: https://forms.gle/4oAjG9MKRTYKX2hP9

New updates every day 💪.