"""
    Screener management system for starting & stopping long term monitoring
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

import typing
from typing import List
from blankly.frameworks.screener.screener_runner import ScreenerRunner
from blankly.utils.utils import load_deployment_settings

import blankly
from blankly.exchanges.exchange import Exchange
from blankly.frameworks.screener.screener_state import ScreenerState
from copy import deepcopy


class Screener:
    def __init__(self, exchange: Exchange,
                 evaluator: typing.Callable,
                 symbols: List[str],
                 init: typing.Callable = None,
                 final: typing.Callable = None,
                 formatter: typing.Callable = None):
        """
        Create a new screener.

        Function Signatures:
        init(screener_state: blankly.ScreenerState)
        evaluator(symbol: str, screener_state: blankly.ScreenerState)
        final(ScreenerState: blankly.ScreenerState)
        formatter(raw_results: dict, screener_state: blankly.ScreenerState)

        This heavily differs from Strategy objects. While a Strategy is optimized for the implementation of
         short or long-term trading strategies, a Screener is optimized for long-term monitoring & reporting of many
         symbols. Screeners are designed to be scheduled to run over intervals of days & weeks. When deployed live,
         a screener-based script will only start when scheduled, then exit entirely.

        Args:
            exchange: An exchange object to construct the screener on
            evaluator: The function that can take information about a screener & classify that screener based on
             parameters
            symbols: A list of symbols to run on.
            init: Optional setup code to run when the program starts
            final: Optional teardown code to run before the program finishes. This will be run every time the
             screener finishes a cycle
            formatter: Optional formatting function that pretties the results form the evaluator
        """

        if not blankly.is_deployed and blankly._screener_runner is None:
            cron_settings = load_deployment_settings()['screener']['schedule']
            blankly._screener_runner = ScreenerRunner(cron_settings)

        # TODO export the symbols here as a list
        self.exchange = exchange
        self.symbols = symbols

        # Store callables as a dictionary
        self.__callables = {
            'evaluator': evaluator,
            'init': init,
            'teardown': final,
            'formatter': formatter
        }
        self.interface = exchange.interface

        # Creat the screener state and pass in this screener object
        self.screener_state = ScreenerState(self)

        self.raw_results = {}
        self.formatted_results = {}

        # Note that only a single screener can be exported at a time for a model
        if blankly.is_deployed:
            blankly.reporter.export_screener(self)

        self.__run()

    def __run(self):
        init = self.__callables['init']
        if callable(init):
            init(self.screener_state)

        self.symbols = self.screener_state.symbols

        # Evaluate using the evaluator function
        # 'symbol': {
        #     # This can all be custom
        #     'classification': 'pass/fail or True / False'
        #     'notes': {
        #         'custom_note': 'this stock was cool'
        #         'current_rsi': .45
        #     }
        # }

        evaluator = self.__callables['evaluator']
        if not callable(evaluator):
            raise TypeError("Must pass a callable for the evaluator.")

        for i in self.symbols:
            # Parse the types for the symbol
            # If it's a dictionary it's A ok but if it's a non-dict give it the value column
            result = evaluator(i, self.screener_state)
            if not isinstance(result, dict):
                result = {
                    'value': result
                }
            self.raw_results[i] = result

        self.symbols = self.screener_state.symbols

        # Copy the evaluator results so that they can be formatted
        self.formatted_results = deepcopy(self.raw_results)

        formatter = self.__callables['formatter']
        if callable(formatter):
            # Mutate the copied dictionary
            self.formatted_results = formatter(self.formatted_results, self.screener_state)

        self.symbols = self.screener_state.symbols

        teardown = self.__callables['teardown']
        if callable(teardown):
            teardown(self.screener_state)

        self.symbols = self.screener_state.symbols

        blankly.reporter.export_screener_result(self)

    def notify(self, message: str = None):
        """
        Send an email and text message to yourself. When deployed live this will come from an official blankly email &
         phone number. When run locally it will use information found in your notify.json file.
         **Note that you need the SMTP configuration to send text messages

        Args:
            message: Optionally fill this with a different string to notify with. If not filled it will notify using the
             formatted results evaluated on construction
        """
        use_str = self.formatted_results
        if message is not None:
            use_str = message

        blankly.reporter.email(use_str)

        blankly.reporter.text(use_str)
