"""
    Signal management system for starting & stopping long term monitoring
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
from blankly.frameworks.signal.signal_runner import SignalRunner

import blankly
from blankly.exchanges.exchange import Exchange
from blankly.frameworks.signal.signal_state import SignalState
from copy import deepcopy


class Signal:
    def __init__(self, exchange: Exchange,
                 evaluator: typing.Callable,
                 symbols: List[str],
                 resolution: typing.Union[str, float],
                 init: typing.Callable = None,
                 final: typing.Callable = None,
                 formatter: typing.Callable = None):
        """
        Create a new signal.

        Function Signatures:
        init(signal_state: blankly.SignalState)
        evaluator(symbol: str, signal_state: blankly.SignalState)
        final(signalState: blankly.SignalState)
        formatter(raw_results: dict, signal_state: blankly.SignalState)

        This heavily differs from Strategy objects. While a Strategy is optimized for the implementation of
         short or long-term trading strategies, a Signal is optimized for long-term monitoring & reporting of many
         symbols. Signals are designed to be scheduled to run over intervals of days & weeks. When deployed live,
         a signal-based script will only start when scheduled, then exit entirely.

        Args:
            exchange: An exchange object to construct the signal on
            evaluator: The function that can take information about a signal & classify that signal based on parameters
            symbols: A list of symbols to run on.
            resolution: The resolution for the signal to run like '1w' or '3d' or 86400
            init: Optional setup code to run when the program starts
            final: Optional teardown code to run before the program finishes. This will be run every time the
             signal finishes a cycle
            formatter: Optional formatting function that pretties the results form the evaluator
        """
        self.resolution = blankly.utils.time_interval_to_seconds(resolution)

        if not blankly.is_deployed and blankly._signal_runner is None:
            blankly._signal_runner = SignalRunner(self.resolution)

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

        # Creat the signal state and pass in this signal object
        self.signal_state = SignalState(self)

        self.raw_results = {}
        self.formatted_results = {}

        # Note that only a single signal can be exported at a time for a model
        if blankly.is_deployed:
            blankly.reporter.export_signal(self)

        self.__run()

    def __run(self):
        init = self.__callables['init']
        if callable(init):
            init(self.signal_state)

        self.symbols = self.signal_state.symbols

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
            self.raw_results[i] = evaluator(i, self.signal_state)

        self.symbols = self.signal_state.symbols

        # Copy the evaluator results so that they can be formatted
        self.formatted_results = deepcopy(self.raw_results)

        formatter = self.__callables['formatter']
        if callable(formatter):
            # Mutate the copied dictionary
            self.formatted_results = formatter(self.formatted_results, self.signal_state)

        self.symbols = self.signal_state.symbols

        teardown = self.__callables['teardown']
        if callable(teardown):
            teardown(self.signal_state)

        self.symbols = self.signal_state.symbols

        blankly.reporter.export_signal_result(self)

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
