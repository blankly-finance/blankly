from Coinbase_Pro.Coinbase_Pro_API import API as API
from API_Interface import API as Interface_API
class Coinbase_Pro:
    def __init__(self, name, API_KEY, API_SECRET, API_PASS):
        self.__exchange = "coinbase_pro"
        self.API_KEY = API_KEY
        self.API_SECRET = API_SECRET
        self.API_PASS = API_PASS
        self.__name = name
        # Create an authenticated object that the interface can use
        self.__calls = API(self.API_KEY, self.API_SECRET, self.API_PASS)
        self.__interface = Interface_API(self)

    def get_exchange(self):
        return self.__exchange

    def get_name(self):
        return self.__name

    def getCalls(self):
        return self.__calls

    def run_command(self, command, args):
        argument_array = args
        return self.__interface.run_command(command, argument_array)