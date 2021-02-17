class API:
    def __init__(self, exchange_object):
        self.__object = exchange_object
        self.__calls = exchange_object.getCalls()

    def run_command(self, command, argument_array):
        if (command == "get_accounts"):
            if (self.__object.get_exchange() == "coinbase_pro"):
                return self.__calls.getAccounts()