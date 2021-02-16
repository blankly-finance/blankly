class API:
    def __init__(self, exchange_object):
        self.__calls = exchange_object.getCalls()

    def runCommand(self, command, **kwargs):
        pass