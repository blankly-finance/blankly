"""
    This class is able to maintain the state of the process and run signals when needed
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

import time
import runpy
import os
from blankly.utils.scheduler import Scheduler
import __main__


class SignalRunner:
    def __init__(self, resolution: float):
        self.__main = __main__.__file__

        self.__resolution = resolution

        self.__scheduler = Scheduler(self.execute, resolution)

    def execute(self):
        # Offset the entire execute cycle by one because this doesn't run the first time
        time.sleep(self.__resolution)
        # The execute function to run the modules
        main_script_abs = os.path.abspath(self.__main)
        runpy.run_path(main_script_abs, {}, "__main__")

    def stop(self):
        self.__scheduler.stop_scheduler()
