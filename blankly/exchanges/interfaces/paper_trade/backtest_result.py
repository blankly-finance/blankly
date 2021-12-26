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
    def __init__(self, history_and_returns: dict, metrics: dict, user_callbacks: dict, trades: dict, history: dict,
                 start_time: float, stop_time: float, quote_currency: str):
        # This can use a ton of memory if these attributes are not cleared
        self.history_and_returns = history_and_returns
        self.metrics = metrics
        self.user_callbacks = user_callbacks
        self.trades = trades
        self.history = history

        self.quote_currency = quote_currency

        self.start_time = start_time
        self.stop_time = stop_time

    def get_account_history(self) -> DataFrame:
        return self.history_and_returns['history']

    def get_returns(self) -> DataFrame:
        return self.history_and_returns['returns']

    def get_resampled_account(self) -> DataFrame:
        return self.history_and_returns['resampled_account_value']

    def get_user_callback_results(self) -> dict:
        return self.user_callbacks

    def get_metrics(self) -> dict:
        return self.metrics

    def __str__(self):
        return_string = "\n"
        return_string += "Historical Dataframes: \n"

        return_string += "Account History: \n"
        return_string += self.history_and_returns['history'].__str__()
        return_string += "\n"

        return_string += "Account Returns: \n"
        return_string += self.history_and_returns['returns'].__str__()
        return_string += "\n"

        return_string += "Resampled Account Value: \n"
        return_string += self.history_and_returns['resampled_account_value'].__str__()
        return_string += "\n"

        return_string += "Blankly Metrics: \n"
        for i in self.metrics.keys():
            spaces_needed = 33 - len(i)
            user_metrics_line = i + ": " + (' ' * spaces_needed) + str(self.metrics[i])
            if i[-3:] == "(%)":
                user_metrics_line += "%"
            user_metrics_line += "\n"
            return_string += user_metrics_line

        if self.user_callbacks != {}:
            return_string += "\n"
            return_string += "User Callbacks: \n"
            for i in self.user_callbacks.keys():
                return_string += i + ": " + str(self.user_callbacks[i]) + "\n"

        return return_string
