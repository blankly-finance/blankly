from Coinbase_Pro_API import API as Coinbase_API
class Coinbase_Pro:
    def __init__(self, name, API_KEY, API_SECRET, API_PASS):
        self.API_KEY = API_KEY
        self.API_SECRET = API_SECRET
        self.API_PASS = API_PASS
        self.__name = name
        self.__calls = Coinbase_API(self.API_KEY, self.API_SECRET, self.API_PASS)

    def getCalls(self):
        return self.__calls

    def getName(self):
        return self.__name