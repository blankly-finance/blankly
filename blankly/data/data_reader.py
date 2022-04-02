"""
    A reader for handling a variety of data formats
    Copyright (C) 2022  Emerson Dove

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
import enum as __enum

from . import DataTypes


class FileTypes(__enum):
    json = 'json'
    csv = 'csv'


"""
This class seeks to solve these problems:

- Read in custom price data for keyless exchange
- Read in event-based
"""


class DataReader:
    @staticmethod
    def is_price_data(data_type: DataTypes) -> bool:
        return data_type == DataTypes.ohlcv_json or data_type == DataTypes.ohlcv_json

    @staticmethod
    def get_file_type(data_type: DataTypes) -> str:
        if data_type == DataTypes.ohlcv_json or data_type == DataTypes.ohlcv_csv:
            return FileTypes.json
        else:
            return FileTypes.csv

    @staticmethod
    def __parse_json(input_: str) -> dict:
        return json.loads(input_)

    def __init__(self, filepath: str, data_type: DataTypes):
        self.input_type = data_type
        self.path = filepath
        self.price_data = self.is_price_data(data_type)
        self.__data = None

    def parse(self):
        if self.type == DataTypes.ohlcv_json:
            contents = self.__parse_json(self.__data)
