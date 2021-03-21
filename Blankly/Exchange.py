"""
    Inherited exchange object.
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
import json


class Exchange:
    def __init__(self, exchange_type, exchange_name):
        self.__name = exchange_name
        self.__type = exchange_type
        try:
            f = open("Settings.json",)
            self.__preferences = json.load(f)
        except FileNotFoundError as e:
            raise FileNotFoundError("Make sure a Settings.json file is placed in the same folder as the project "
                                    "working directory!")


    def get_name(self):
        return self.__name

    def get_type(self):
        return self.__type

    def get_preferences(self):
        return self.__preferences

    def start_models(self, coin=None):
        """
        Start all models or a specific one after appending it to to the exchange
        """
        if coin is not None:
            # Run a specific model with the args
            if not self.models[coin]["model"].is_running():
                self.models[coin]["model"].run(self.models[coin]["args"])
            return "Started model attached to: " + coin
        else:
            for coin_iterator in self.models:
                # Start all models
                if not self.models[coin_iterator]["model"].is_running():
                    self.models[coin_iterator]["model"].run(self.models[coin_iterator]["args"])
                else:
                    print("Ignoring the model on " + coin_iterator)
            return "Started all models"
