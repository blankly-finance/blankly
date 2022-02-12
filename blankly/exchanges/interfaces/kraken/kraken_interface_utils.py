import json
from pathlib import Path
from blankly.exchanges.interfaces.kraken.kraken_api import API as KrakenAPI
from blankly.exchanges.interfaces.kraken.kraken_auth import KrakenAuth


def kraken_api() -> KrakenAPI:
    keys_file_path = Path("./tests/config/keys.json")

    auth_obj = KrakenAuth(str(keys_file_path), "default")
    api = KrakenAPI(auth_obj)
    return api


def blankly_symbol_to_kraken_symbol(blankly_symbol: str):
    api = kraken_api()
    response = api.asset_pairs()
    
    
    for key, value in response.items():
        
        wsname = value["wsname"].replace("/", "-")
        
        if wsname == blankly_symbol:
            return key
        
    raise ValueError("Invalid blankly symbol")

def kraken_symbol_to_blankly_symbol(kraken_symbol: str):
    api = kraken_api()
    response = api.asset_pairs()
    
    for key, value in response.items():
        if key == kraken_symbol or value["altname"] == kraken_symbol:
            return value["wsname"].replace("/", "-")
        
    raise ValueError("Invalid kraken symbol")