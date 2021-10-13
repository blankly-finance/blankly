"""
    Custom API for interacting with the frontend API routes
    Copyright (C) 2021  Emerson Dove

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import requests
from blankly.utils.utils import info_print

blankly_frontend_api_url = "http://localhost:3000"


class API:
    def __init__(self, token, override_url: str = None):
        if override_url:
            self.url = override_url
        else:
            self.url = blankly_frontend_api_url

        self.token = None
        self.token = self.exchange_token(token)

    def __request(self, type_: str, route: str, json: dict = None, params: dict = None, file=None, data: dict = None):
        """
        Create a general request to the blankly API services

        Args:
            type_: Request types such as 'post', 'get', and 'delete'
            route: The address where the request should be routed to './model/details'
            json: Optional json to be attached to the request
            params: Optional parameters for the address URL
            data: Optional JSON to be attached to the request body dictionary
            file: Optional file uploaded in bytes: file = {'file': open(file_path, 'rb')}
        """
        url = self.url
        if url[-1] != '/' and route[0] != '/':
            url += '/'
        url += route

        kwargs = {
            'url': url,
            'params': params,
            'json': json,
            'files': file,
            'data': data,
        }

        # Add the token if we have it
        if self.token is not None:
            kwargs['headers'] = {'token': self.token}

        try:
            if type_ == "get":
                out = requests.get(**kwargs)
            elif type_ == "post":
                out = requests.post(**kwargs)
            elif type_ == "delete":
                out = requests.delete(**kwargs)
            else:
                raise LookupError("Request type is not implemented or does not exist.")
        except requests.exceptions.ConnectionError:
            raise requests.exceptions.ConnectionError("Failed to connect to deployment service.")

        try:
            return out.json()
        except ValueError:
            print(f'Invalid Response: {out}')
            return None

    def exchange_token(self, token):
        """
        Get the JWT from the refresh token
        """
        return self.__request('post', 'auth/token', data={'refreshToken': token})['idToken']

    def get_details(self, project_id: str, model_id: str):
        """
        Get the details route
        """
        return self.__request('get', 'model/details', data={'projectId': project_id, 'modelId': model_id})

    def get_status(self, project_id: str, model_id: str):
        return self.__request('get', 'model/status', data={'projectId': project_id, 'modelId': model_id})

    def list_projects(self):
        return self.__request('get', 'project/list')

    def create_project(self, name: str, plan: str):
        return self.__request('post', 'project/create')

    def upload(self, file_path: str, project_id: str, model_id: str):
        file_path = r'{}'.format(file_path)
        file = {'model': open(file_path, 'rb')}
        return self.__request('post', 'model/upload', file=file, data={'projectId': project_id,
                                                                       'modelId': model_id}, params={'flag': True})
