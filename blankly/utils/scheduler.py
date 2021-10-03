"""
    Class for the creation of a scheduler in main.
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
import threading
import time
import traceback
import typing
from datetime import datetime as dt

from blankly.utils.time_builder import time_interval_to_seconds
from blankly.utils.utils import ceil_date
from blankly.utils.utils import info_print


class Scheduler:
    def __init__(self, function: typing.Callable,
                 interval: typing.Union[str, float],
                 initially_stopped: bool = False,
                 synced: bool = False, **kwargs):
        """
        Wrapper for functions that run at a set interval
        Args:
            function: Function reference to create the scheduler on ex: self.price_event
            interval: int of delay between calls in seconds, or a string that takes units s, m, h, d w, M, y (second,
              minute, hour, day, week, month, year) after a magnitude. examples: "4s", "6h", "10d".
            initially_stopped: Keep the scheduler halted until start() is run
            synced: Align the scheduler with intervals in UTC. ex: if the interval is '1h' then with sync it will only
              run at *:00
        """
        if isinstance(interval, str):
            interval = time_interval_to_seconds(interval)

        # Stop flag
        self.__stop = False
        self.__thread = None
        self.synced = synced

        self.__interval = interval
        self.__kwargs = kwargs
        self.__callback = function

        self.__lock = threading.Lock()

        if not initially_stopped:
            self.start()

        # This can be used for a statically typed, single-process bot decorator.
        # Leaving this because it probably will be used soon

        # def decorator(function):
        #     @functools.wraps(function)
        #     def wrapper():
        #         thread = threading.Thread(target=threading_wait, args=(function, interval,))
        #         thread.start()
        #     wrapper()
        # return decorator

    def start(self, force=False):
        """
        Start the scheduler.

        Args:
            force: Override multi-thread protection and create more threads of the scheduler callback
        """
        if self.__thread is None or force:
            self.__thread = threading.Thread(target=self.__threading_wait,
                                             args=(self.__callback, self.__interval, self.__kwargs))
            self.__thread.start()
        else:
            info_print("Scheduler already started and force not enabled...skipping start.")

    def get_interval(self):
        """
        Get the seconds between each scheduler run
        """
        return self.__interval

    def make_daemon(self):
        self.__thread.setDaemon(True)

    def get_kwargs(self):
        """
        Get the custom function argument dictionary
        """
        return self.__kwargs

    def stop_scheduler(self):
        """
        Halt the scheduler loop
        """
        self.__stop = True

    def get_callback(self):
        """
        Get the callback function that the scheduler is running on
        """
        return self.__callback

    def __threading_wait(self, func, interval, kwargs):
        """
        This function is used with the scheduler decorator
        """
        base_time = time.time()
        if self.synced:
            base_time = ceil_date(dt.now(), seconds=interval).timestamp()
            offset = base_time - time.time()
            time.sleep(offset)
            kwargs['ohlcv_time'] = base_time
        while True:
            if self.__stop:
                break
            # This try except is replicated in the backtesting framework
            try:
                func(**kwargs)
            except Exception:
                traceback.print_exc()
            base_time += interval
            if self.synced:
                kwargs['ohlcv_time'] += interval

            # The downside of this is that it keeps the thread running while waiting to stop
            # It's dependent on delay if its more efficient to just check more
            offset = base_time - time.time()
            if offset < 0:
                offset = 0
            time.sleep(offset)
