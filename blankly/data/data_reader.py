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
from enum import Enum

from . import DataTypes

"""
This class seeks to solve these problems:

- Read in custom price data for keyless exchange
- Read in event-based
"""


class FileTypes(Enum):
    csv = 'csv'
    json = 'json'


class __DataReader:
    @staticmethod
    def _check_length(df: pd.DataFrame, identifier: str):
        try:
            assert (len(df) > 2)
        except AssertionError:
            raise AssertionError(f"Must give data with at least 2 rows in {identifier}.")

    @staticmethod
    def __is_price_data(data_type: DataTypes) -> bool:
        return data_type == DataTypes.ohlcv_json or data_type == DataTypes.ohlcv_csv

    @property
    def data(self):
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
        self._internal_dataset = {}
        self.type: DataTypes = data_type
        self.price_data: bool = self.__is_price_data(data_type)


class PriceReader(__DataReader):
    def __parse_json_prices(self, file_paths: list) -> None:
        for file in file_paths:
            # Load the contents into json first because it has a ton of symbols
            contents = json.loads(open(file).read())

            for symbol in contents:
                self._write_dataset(contents, symbol, ('open', 'high', 'low', 'close', 'volume', 'time'))

                self._check_length(self._internal_dataset[symbol], file)

                # Ensure that the dataframe is sorted by time
                self._internal_dataset[symbol] = self._internal_dataset[symbol].sort_values('time')

    def __parse_csv_prices(self, file_paths: list, symbols: list) -> None:
        if symbols is None:
            raise LookupError("Must pass one or more symbols to identify the csv files")
        if len(file_paths) != len(symbols):
            raise LookupError(f"Mismatching symbol & file path lengths, got {len(file_paths)} and {len(symbols)} for "
                              f"file paths and symbol lengths.")

        for index in range(len(file_paths)):
            # Load the file via pandas
            contents = pd.read_csv(file_paths[index])

            self._check_length(contents, file_paths[index])

            # Check if its contained
            assert ({'open', 'high', 'low', 'close', 'volume', 'time'}.issubset(contents.columns))

            # Now push it directly into the dataset and sort by time
            self._internal_dataset[symbols[index]] = contents.sort_values('time')

    @staticmethod
    def __associate(file_paths: list) -> str:
        file_type = ''

        def complain_if_different(ending_: str, type_: str):
            nonlocal file_type
            if file_type == '':
                file_type = type_
            elif file_type is not None and file_type != ending_:
                raise LookupError("Cannot pass both csv files and json files into a single constructor.")

        for file_path in file_paths:
            if file_path[-3:] == 'csv':
                complain_if_different('csv', FileTypes.csv.value)
            elif file_path[-4:] == 'json':
                # In this instance the symbols should be None
                complain_if_different('json', FileTypes.json.value)
            else:
                raise LookupError(f"Unknown filetype for {file_path}")

        return file_type

    def _guess_resolutions(self):
        for symbol in self._internal_dataset:
            # Get the time diff
            time_series: pd.Series = self._internal_dataset[symbol]['time']
            time_dif = time_series.diff()

            # Now find the most common difference and use that
            if symbol not in self.prices_info:
                self.prices_info[symbol] = {}

            # Store the resolution start time and end time of each dataset
            self.prices_info[symbol]['resolution'] = int(time_dif.value_counts().idxmax())
            self.prices_info[symbol]['start_time'] = time_series.iloc[0]
            self.prices_info[symbol]['stop_time'] = time_series.iloc[-1]

    def __init__(self, file_path: [str, list], symbol: [str, list] = None):
        """
        Read in a new custom price dataset in either json or csv format

        Args:
            file_path (str or list): A single file path or list of filepaths pointing to a set of price data
            symbol (str or list): Only required if using .csv files. These must match in index to the symbol that the
             csv file path corresponds to. The CSV files also must have at least 2 rows of data in them.

            symbol (str or list): Pass the symbol or symbols that the file paths correspond to. One file path and one
             symbol can be passed as a non list but multiple can be passed as lists in both arguments. Just make sure
             that the symbol indices match on both arguments
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

        # Empty dict to store the resolutions of the inputs by symbol
        self.prices_info = {}

        try:
            assert(len(symbols) == len(set(symbols)))
        except AssertionError:
            raise AssertionError("Cannot use duplicate symbols for one price reader. Please use multiple price readers"
                                 " to read in different datasets of the same symbol.")

        data_type = self.__associate(file_paths)

        super().__init__(data_type)

        if data_type == FileTypes.json.value:
            self.__parse_json_prices(file_paths)
        elif data_type == FileTypes.csv.value:
            self.__parse_csv_prices(file_paths, symbols)
        else:
            raise LookupError("No parsing written for input type.")

        self._guess_resolutions()


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
