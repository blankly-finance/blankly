import numpy as np
import pickle
from pathlib import Path
import unittest
from Blankly.indicators import ema, vwma, wma, zlema, sma, hma, kaufman_adaptive_ma, trima, macd

def compare_equal(a, b):
    # compares two numpy arrays
    return np.array_equal(a, b)

class MovingAverages(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        data_path = Path("tests/config/test_data.p").resolve()
        with open(data_path, 'rb') as f:
            cls.data = pickle.load(f)
        
    def test_one_param_moving_averages(self):
        period = self.data['periods'][0]

        ema_res = ema(self.data['close'], period)
        self.assertTrue(compare_equal(ema_res, self.data[period]['ema']))

        wma_res = wma(self.data['close'], period)
        self.assertTrue(compare_equal(wma_res, self.data[period]['wma']))

        zlema_res = zlema(self.data['close'], period)
        self.assertTrue(compare_equal(zlema_res, self.data[period]['zlema']))

        sma_res = sma(self.data['close'], period)
        self.assertTrue(compare_equal(sma_res, self.data[period]['sma']))

        hma_res = hma(self.data['close'], period)
        self.assertTrue(compare_equal(hma_res, self.data[period]['hma']))

        kaufman_res = kaufman_adaptive_ma(self.data['close'], period)
        self.assertTrue(compare_equal(kaufman_res, self.data[period]['kaufman_adaptive_ma']))

        trima_res = trima(self.data['close'], period)
        self.assertTrue(compare_equal(trima_res, self.data[period]['trima']))

    def test_one_param_moving_averages_diff_period(self):
        period = self.data['periods'][1]

        ema_res = ema(self.data['close'], period)
        self.assertTrue(compare_equal(ema_res, self.data[period]['ema']))

        wma_res = wma(self.data['close'], period)
        self.assertTrue(compare_equal(wma_res, self.data[period]['wma']))

        zlema_res = zlema(self.data['close'], period)
        self.assertTrue(compare_equal(zlema_res, self.data[period]['zlema']))

        sma_res = sma(self.data['close'], period)
        self.assertTrue(compare_equal(sma_res, self.data[period]['sma']))

        hma_res = hma(self.data['close'], period)
        self.assertTrue(compare_equal(hma_res, self.data[period]['hma']))

        kaufman_res = kaufman_adaptive_ma(self.data['close'], period)
        self.assertTrue(compare_equal(kaufman_res, self.data[period]['kaufman_adaptive_ma']))

        trima_res = trima(self.data['close'], period)
        self.assertTrue(compare_equal(trima_res, self.data[period]['trima']))

    def test_macd(self):
        short_period = self.data['short_period']
        long_period = self.data['long_period']
        for period in self.data['periods']:
            macd_res = macd(self.data['close'], short_period, long_period, period)
            self.assertTrue(compare_equal(macd_res, self.data[period]['macd']))

    def tests_vwma(self):
        volume = self.data['volume']
        for period in self.data['periods']:
            vwma_res = vwma(self.data['close'], volume, period)
            self.assertTrue(compare_equal(vwma_res, self.data[period]['vwma']))