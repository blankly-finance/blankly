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
import os

blankly_frontend_api_url = "http://localhost:3000"


class API:
    def __init__(self, override_url: str = None):
        if override_url:
            self.url = override_url
        else:
            self.url = blankly_frontend_api_url

    def __request(self, type_: str, route: str, json: dict = None, params: dict = None, file=None):
        """
        Create a general request to the blankly API services

        Args:
            type_: Request types such as 'post', 'get', and 'delete'
            route: The address where the request should be routed to './model/details'
            json: Optional json to be attached to the request body
            params: Optional parameters for the address URL
            file: Optional file uploaded in bytes: file = {'file': open(file_path, 'rb')}
        """
        route = os.path.join(self.url, route)

        kwargs = {
            'url': route,
            'params': params,
            'json': json,
            'files': file
        }

        if type_ == "get":
            out = requests.get(**kwargs)
        elif type_ == "post":
            out = requests.post(**kwargs)
        elif type_ == "delete":
            out = requests.delete(**kwargs)
        else:
            raise LookupError("Request type is not implemented or does not exist.")

        return out.json()

    def get_details(self, project_id: str, model_id: str):
        """
        Get the details route
        """
        return self.__request('get', 'model/details', json={'projectId': project_id, 'modelId': model_id})

    def get_status(self, project_id: str, model_id: str):
        return self.__request('get', 'model/status', json={'projectId': project_id, 'modelId': model_id})

    def list_projects(self, uid: str):
        return self.__request('get', 'project/list', json={'uid': uid})

    def create_project(self, uid: str, name: str, plan: str):
        return self.__request('post', 'project/create', json={'uid': uid, 'name': name, 'plan': plan})

    def upload(self, file_path: str):
        file = {'file': open(file_path, 'rb')}
        return self.__request('post', 'model/upload', file=file)

