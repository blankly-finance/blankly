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

import json

import requests
from blankly.utils.utils import info_print

blankly_deployment_url = 'https://deploy.blankly.finance'


class API:
    def __init__(self, token, override_url: str = None):
        if override_url:
            self.url = override_url
        else:
            self.url = blankly_deployment_url

        self.token = None
        self.auth_data = self.exchange_token(token)

        self.token = self.auth_data['idToken']
        self.user_id = self.auth_data['data']['user_id']

    def __request(self, type_: str, route: str, json_: dict = None, params: dict = None, file=None, data: dict = None):
        """
        Create a general request to the blankly API services

        Args:
            type_: Request types such as 'post', 'get', and 'delete'
            route: The address where the request should be routed to './model/details'
            json_: Optional json to be attached to the request
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
            'json': json_,
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

        # Show info that the request was not authorized but still
        #  allow the process to continue
        if out.status_code == 401:
            info_print("Unauthorized request.")

        try:
            return out.json()
        except ValueError:
            print(f'Invalid Response: {out}')
            return None

    def exchange_token(self, token):
        """
        Get the JWT from the refresh token
        """
        return self.__request('post', 'auth/token', data={'refreshToken': token})

    def get_details(self, model_id: str):
        """
        Get the details route
        """
        return self.__request('post', 'model/details', data={'modelId': model_id})

    def get_status(self):
        return self.__request('get', 'model/status')

    def list_projects(self):
        return self.__request('get', 'project/list')

    def get_plans(self, type_: str):
        """
        Args:
            type_: Can be 'backtesting' or 'live'
        """
        return self.__request('post', 'project/plans', data={'type': type_})

    def create_project(self, name: str, description: str):
        return self.__request('post', 'project/create', data={'name': name,
                                                              'description': description})

    def deploy(self, file_path: str, plan: str, project_id, model_id: str,
               general_description: str, version_description: str, name: str, create_new: bool,
               python_version: float):
        file_path = r'{}'.format(file_path)
        file = {'model': open(file_path, 'rb')}
        return self.__request('post', 'model/deploy', file=file, data={'plan': plan,
                                                                       'name': name,
                                                                       'modelId': model_id,
                                                                       'projectId': project_id,
                                                                       'generalDescription': general_description,
                                                                       'versionDescription': version_description,
                                                                       'createNew': create_new,
                                                                       'pythonVersion': str(python_version)})

    def backtest_deployed(self, project_id: str, model_id: str, args: dict, version_id: str, backtest_description: str):
        return self.__request('post', 'model/backtestUploadedModel',
                              json_={'projectId': project_id,
                                     'modelId': model_id,
                                     'versionId': version_id,
                                     'backtestArgs': args,
                                     'backtestDescription': backtest_description})

    def backtest(self, file_path: str, project_id: str, model_id: str, args: dict, plan: str,
                 create_new: bool, name: str, python_version: float, backtest_description: str = ""):
        file_path = r'{}'.format(file_path)
        file = {'model': open(file_path, 'rb')}
        return self.__request('post', 'model/backtest', file=file,
                              data={'projectId': project_id,
                                    'modelId': model_id,
                                    'plan': plan,
                                    'backtestDescription': backtest_description,
                                    'backtestArgs': json.dumps(args),
                                    'createNew': create_new,
                                    'name': name,
                                    'pythonVersion': str(python_version)})

    def signal(self):
        return self.__request('get', 'model/signalTest')
