from multiprocessing import Process
import time, fbprophet
import Utils, Tickers, Exchange
from API_Interface import APIInterface


class Predictor:
    def __init__(self, exchangeType):
        self.__exchangeType = exchangeType
        # Start the process
        p = Process(target=self.__runPredictor)
        p.start()
        p.join()

    def __runPredictor(self):
        # Main loop, running on different thread
        while True:
            time.sleep(1)
            print("predicting stuff...")