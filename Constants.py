""" BTC """
MINIMUM_BUY_SELL = .001
CURRENT_HIGHEST_USD = 42000

""" Coinbase """
# This is currently set to the actual fee rate, sometimes .0002 (.02%) is added as padding.
PRETEND_FEE_RATE = .005

# Actual fee rates
TAKER_FEE_RATE = .005
MAKER_FEE_RATE = .005

""" Margins """
# This is used with the fee rate. This allows a guaranteed profit if it reaches past fees and this extra rate
SELL_MIN = .002

""" Settings """
EMERGENCY_SELL_SAMPLE = 10
