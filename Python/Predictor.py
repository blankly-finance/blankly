from multiprocessing import Process
import time, fbprophet


class Predictor:
    def __init__(self):
        p = Process(target=self.__runPredictor)
        p.start()
        p.join()

    def __runPredictor(self):
        while True:
            time.sleep(1)
            print("predicting stuff...")