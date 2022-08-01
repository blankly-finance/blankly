from blankly.futures import FTXFutures

ftxFutures = FTXFutures()

symbols = ['BTC-PERP', 'ETH-PERP']
for symbol in symbols:
    ftxFutures.interface.history('BTC-PERP', '1y', resolution='1d')