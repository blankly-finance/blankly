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
import pandas as pd
from typing import Dict

from . import DataTypes

"""
This class seeks to solve these problems:

- Read in custom price data for keyless exchange
- Read in event-based
"""


class __DataReader:
    @staticmethod
    def __is_price_data(data_type: DataTypes) -> bool:
        return data_type == DataTypes.ohlcv_json or data_type == DataTypes.ohlcv_csv

    @property
    def data(self) -> Dict[pd.DataFrame]:
        return self._internal_dataset

    def _write_dataset(self, contents: dict, key: str, required_columns: tuple):
        try:
            # Check if all the keys exist for each part of the dictionary
            assert (all(key in contents[key] for key in required_columns))
        except AssertionError as e:
            raise AssertionError(f"Must have at least these columns: f{required_columns} for {key}"
                                 f" with error {e}")
        self._internal_dataset[key] = pd.DataFrame.from_dict(contents[key])

    def __init__(self, data_type: [DataTypes, str]):
        self._internal_dataset = None
        self.type: DataTypes = data_type
        self.price_data: bool = self.__is_price_data(data_type)


class PriceReader(__DataReader):
    def __parse_json_prices(self, file_paths: list) -> None:
        for file in file_paths:
            # Load the contents into json first because it has a ton of symbols
            contents = json.loads(open(file).read())

            for symbol in contents:
                self._write_dataset(contents, symbol, ('open', 'high', 'low', 'close', 'volume', 'time'))

    def __parse_csv_prices(self, file_paths: list, symbols: list) -> None:
        if symbols is None:
            raise LookupError("Must pass one or more symbols to identify the csv files")
        if len(file_paths) != len(symbols):
            raise LookupError(f"Mismatching symbol & file path lengths, got {len(file_paths)} and {len(symbols)} for "
                              f"file paths and symbol lengths.")

        for index in range(len(file_paths)):
            # Load the file via pandas
            contents = pd.read_csv(file_paths[index])

            # Check if its contained
            assert ({'open', 'high', 'low', 'close', 'volume', 'time'}.issubset(contents.columns))

            # Now push it directly into the dataset
            self._internal_dataset[symbols[index]] = contents

    @staticmethod
    def __associate(file_paths: list) -> str:
        data_type = ''

        def complain_if_different(ending_: str, type_: DataTypes):
            nonlocal data_type
            if data_type == '':
                data_type = type_
            elif data_type is not None and data_type != ending_:
                raise LookupError("Cannot pass both csv files and json files into a single constructor.")

        for file_path in file_paths:
            ending = file_path[-4:]
            if ending == '.csv':
                complain_if_different('.csv', DataTypes.ohlcv_csv)
            elif ending == 'json':
                # In this instance the symbols should be None
                complain_if_different('json', DataTypes.ohlcv_json)
            else:
                raise LookupError(f"Unknown ending {ending}")

        return data_type

    def __init__(self, file_path: [str, list], symbol: [str, list] = None):
        """
        Read in a new custom price dataset in either json or csv format

        Args:
            file_path (str or list): A single file path or list of filepaths pointing to a set of price data
            symbol (str or list): Only required if using .csv files. These must match in index to the symbol that the
             csv file path corresponds to
        """
        # Turn it into a list
        if isinstance(file_path, str):
            file_paths = [file_path]
        else:
            file_paths = file_path

        if isinstance(symbol, str):
            symbols = [symbol]
        else:
            # Could be None still
            symbols = symbol

        data_type = self.__associate(file_paths)

        super().__init__(data_type)

        if data_type == DataTypes.ohlcv_json:
            self.__parse_json_prices(file_paths)
        elif data_type == DataTypes.ohlcv_csv:
            self.__parse_csv_prices(file_paths, symbols)
        else:
            raise LookupError("No parsing written for input type.")


class EventReader(__DataReader):
    def __parse_json_events(self, file_path):
        contents = json.loads(file_path)

        for event_type in contents:
            self._write_dataset(contents, event_type, ('time', 'data'))

    def __init__(self, file_path):
        try:
            assert file_path[-3:] == 'csv'
        except AssertionError:
            raise AssertionError(f"The filepath did not have a \'csv\' ending - got: {file_path[-3:]}")

        super().__init__(DataTypes.event_json)
