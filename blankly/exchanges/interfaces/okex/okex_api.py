import base64
import hashlib
import hmac
import json
import time

import requests
from requests.auth import AuthBase

# Create custom authentication for Exchange
from blankly.utils.utils import info_print


class OkexExchangeAuth(AuthBase):
    # Provided by CBPro: https://docs.pro.coinbase.com/#signing-a-message
    def __init__(self, api_key, api_secret, api_pass):
        self.api_key = api_key
        self.secret_key = api_secret
        self.passphrase = api_pass

    def __call__(self, request):
        timestamp = str(time.time())
        message = ''.join([timestamp, request.method,
                           request.path_url, (request.body or '')])
        request.headers.update(get_auth_headers(timestamp, message,
                                                self.api_key,
                                                self.secret_key,
                                                self.passphrase))
        return request


def get_auth_headers(timestamp, message, api_key, secret_key, passphrase):
    message = message.encode('ascii')
    hmac_key = base64.b64decode(secret_key)
    signature = hmac.new(hmac_key, message, hashlib.sha256)
    signature_b64 = base64.b64encode(signature.digest()).decode('utf-8')
    return {
        'Content-Type': 'Application/JSON',
        'OK-ACCESS-KEY': api_key,
        'OK-ACCESS-SIGN': signature_b64,
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': passphrase
    }

class API:
    def __init__(self, api_key: str, api_secret: str, api_pass: str, API_URL: str = 'https://www.okex.com/'):
        self.__auth = OkexExchangeAuth(api_key, api_secret, api_pass)
        self.__api_url = API_URL
        self.session = requests.Session()

