def blankly_symbol_to_kraken_symbol(blankly_symbol: str):
    return blankly_symbol.replace('-', '/')


def kraken_symbol_to_blankly_symbol(kraken_symbol: str):
    return kraken_symbol.replace('/', '-')
