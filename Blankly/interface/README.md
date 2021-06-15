## Decisions for return types and values of the Interface class

### get_calls()
- Not relevant 

### get_products()
List for each product:
```json
[
  "currency_id": "BTC-USD",
  "base_currency": "BTC",
  "quote_currency": "USD",
  "base_min_size": "0.01",
  "base_max_size": "10000.00"
]
```

### get_account(account)
```json
[
    {
        "id": "71452118-efc7-4cc4-8780-a5e22d4baa53",
        "currency": "BTC",
        "balance": "0.0000000000000000",
        "available": "0.0000000000000000",
        "hold": "0.0000000000000000"
    },
    {
        ...
    }
]
```
This may be better if users are allowed to search through for a currency because that would remove the need for an ID

### Orders
------- skipped placement


### Cancel order