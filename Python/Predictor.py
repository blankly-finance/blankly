from multiprocessing import process
import time
class Predictor:
    def __init__(self):
        p = process.Process(target = self.__runPredictor)
        p.start()

    def __runPredictor(self):
        while True:
            time.sleep(1)
            print("predicting stuff...")