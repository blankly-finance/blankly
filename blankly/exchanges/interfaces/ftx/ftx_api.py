import requests
from typing import Optional, Dict, Any, List
import urllib.parse
import json
from blankly.exchanges.auth.abc_auth import ABCAuth
import time
import hmac

class API:
    _API_URL = "https://ftx.com/api/"

    def __init__(self, auth: ABCAuth, _subaccount_name = None):

        self.__api_key = auth.keys['API_KEY']
        self.__api_secret = auth.keys['API_SECRET']
        self._subaccount_name = subaccount_name

        self.ftx_session = requests.Session()

    def _signed_request(self, method: str, path: str):
        request = requests.Request(method, self._API_URL + path, **kwargs)
        self._get_signature(request)
        result = self.ftx_session.send(request.prepare())
        return self._handle_response(result)

    def _get_signature(self, request: requests.Request):
        ts = int(1000 * time.time())
        prepared_request = request.prepare()
        signed_data = f'{ts}{prepared_request.method}{prepared_request.path_url}'.encode()

        if prepared_request.body:
            signed_data += prepared_request.body
        
        signature = hmac.new(self.__api_secret.encode(), signed_data, 'sha256').hexdigest()
        
        request.headers.update({
            'FTX-KEY': self.__api_key,
            'FTX-SIGN': signature,
            'FTX-TS': str(ts)
        })

        if self._subaccount_name:
            request.headers.update({
                'FTX-SUBACCOUNT': urllib.parse.quote(self._subaccount_name)
            })

    def _signed_delete(self, path: str, params: Optional[Dict[str, Any]] = None):
        return self._signed_request('DELETE', path, json = params)

    def _signed_get(self, path: str, params: Optional[Dict[str, Any]] = None):
        return self._signed_request('GET', path, params = params)

    def _signed_post(self, path: str, params: Optional[Dict[str, Any]] = None):
        return self._signed_request('POST', path, json = params) 

    def _handle_response(self, response: requests.Response):
        try:
            result = response.json()

        except ValueError:
            response.raise_for_status()
            raise
            
        else:
            if not data['success']:
                raise Exception(data['error'])
            else:
                return data['success']
        


