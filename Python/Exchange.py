import json
"""
This class creates a boilerplate exchange.
"""

class Exchange:
    def __init__(self, exchange_type, exchange_name, user_preferences, model):
        self.__name = exchange_name
        self.__type = exchange_type
        self.__preferences = user_preferences
        self.__model = model

    def get_name(self):
        return self.__name

    def getType(self):
        return self.__type

    def getPreferences(self):
        return self.__preferences

    def get_state(self):
        return (self.__model.get_state()._getvalue())

    def run_model(self, args=None):
        self.__model.run(args)