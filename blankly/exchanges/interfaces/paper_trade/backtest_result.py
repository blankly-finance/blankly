"""
    Object for cleanly storing & printing complex backtest results.
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

from pandas import DataFrame


class BacktestResult:
    def __init__(self, dataframes: dict, metrics: dict, user_callbacks: dict):
        self.dataframes = dataframes
        self.metrics = metrics
        self.user_callbacks = user_callbacks

    def get_account_history(self) -> DataFrame:
        return self.dataframes['history']

    def get_returns(self) -> DataFrame:
        return self.dataframes['returns']

    def get_resampled_account(self) -> DataFrame:
        return self.dataframes['resampled_account_value']

    def get_user_callback_results(self) -> dict:
        return self.user_callbacks

    def get_metrics(self) -> dict:
        return self.metrics

    def __str__(self):
        return_string = "\n"
        return_string += "Historical Dataframes: \n"

        return_string += "Account History: \n"
        return_string += self.dataframes['history'].__str__()
        return_string += "\n"

        return_string += "Account Returns: \n"
        return_string += self.dataframes['returns'].__str__()
        return_string += "\n"

        return_string += "Resampled Account Value: \n"
        return_string += self.dataframes['resampled_account_value'].__str__()
        return_string += "\n"

        return_string += "Blankly Metrics: \n"
        for i in self.metrics.keys():
            return_string += i + ": " + str(self.metrics[i]) + "\n"

        if self.user_callbacks != {}:
            return_string += "\n"
            return_string += "User Callbacks: \n"
            for i in self.user_callbacks.keys():
                return_string += i + ": " + str(self.user_callbacks[i]) + "\n"

        return return_string
