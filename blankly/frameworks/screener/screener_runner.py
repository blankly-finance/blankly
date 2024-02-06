"""
    This class is able to maintain the state of the process and run screeners when needed
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
import datetime
from datetime import timezone
import time
import runpy
import os
import __main__
import threading
from blankly.utils.utils import info_print, trunc


class ScreenerRunner:
    def __init__(self, cronjob: str):
        try:
            from croniter import croniter
            self.croniter = croniter
        except ImportError:
            raise ImportError("To run screeners locally, please \"pip install croniter\".")
        self.__main = __main__.__file__

        self.croniter = self.croniter(cronjob, datetime.datetime.fromtimestamp(time.time()).astimezone(timezone.utc))

        self.__stopped = False

        # Start the execution thread
        threading.Thread(target=self.execute).start()

    def execute(self):
        while True:
            # Sleep until the next
            next_run_datetime = self.croniter.get_next()
            next_run_in = next_run_datetime - time.time()
            info_print(f"Starting screener...the next screener run will be started in {trunc(next_run_in, 2)} "
                       f"seconds or at {datetime.datetime.fromtimestamp(next_run_datetime)}")
            time.sleep(next_run_in)
            if not self.__stopped:
                # Start the screener in a different thread
                threading.Thread(target=self.__executor).start()
            else:
                break

    def __executor(self):
        # The execute function to run the modules
        main_script_abs = os.path.abspath(self.__main)
        runpy.run_path(main_script_abs, {}, "__main__")

    def stop(self):
        self.__stopped = True
