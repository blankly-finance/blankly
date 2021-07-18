## Alpaca Fixes

### get_products()

- Need correct base_min_size
- Need correct base_max_size
- Need a correct base increment that depends on if the equity is fractional
- Needs capital USD (**fixed**)
- Needs correct currency ID (**fixed**)

### get_account()

- Need a correct hold value
    - This is described here https://alpaca.markets/docs/trading-on-alpaca/orders/ in buying power
- Get account with no arguments needs to list every single account, including those with no size at all. This involves
  parsing the products and comparing those to the account output (this may be implemented I can really tell).
- USD also needs to be in there

### market_order()

- Looks great
- Up for debate but isoparse could use the implementation in utils to clear up an import

### limit_order()

- Let it throw the alpaca APIError instead of a warning and returning the wrong type
- Limit order should be `GTC` because all other exchanges are strictly GTC

### cancel_order()

- Looks great to me

### get_open_orders()

- The isolated version is never assigned back to the array unless the reference works here

### get_order()

- Looks great

### get_fees()

- Looks great

### get_product_history()

- Needs to auto round to needed granularity

### get_market_limits()

- Needs doing

### get_price()

- Completely broken

## Also need:

- Ability to support a currency pair or just a single id (`AAPL` or `AAPL-USD`) for all functions
- Timezone checking
- Error printing *using blankly exceptions*