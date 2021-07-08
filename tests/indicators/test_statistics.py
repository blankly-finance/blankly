import pickle
import numpy as np
from pathlib import Path
import unittest
from blankly.indicators import stddev_period, var_period, stderr_period, min_period, max_period

def compare_equal(a, b):
    # compares two numpy arrays
    return np.array_equal(a, b)

class Statistics(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        data_path = Path("tests/config/test_data.p").resolve()
        with open(data_path, 'rb') as f:
            cls.data = pickle.load(f)

    def test_one_param_moving_averages(self):
        period = self.data['periods'][0]

        stddev_res = stddev_period(self.data['close'], period)
        self.assertTrue(compare_equal(stddev_res, self.data[period]['stddev_period']))

        var_res = var_period(self.data['close'], period)
        self.assertTrue(compare_equal(var_res, self.data[period]['var_period']))

        stderr_res = stderr_period(self.data['close'], period)
        self.assertTrue(compare_equal(stderr_res, self.data[period]['stderr_period']))

        min_res = min_period(self.data['close'], period)
        self.assertTrue(compare_equal(min_res, self.data[period]['min_period']))

        max_res = max_period(self.data['close'], period)
        self.assertTrue(compare_equal(max_res, self.data[period]['max_period']))

    def test_one_param_moving_averages_diff_period(self):
        period = self.data['periods'][1]

        stddev_res = stddev_period(self.data['close'], period)
        self.assertTrue(compare_equal(stddev_res, self.data[period]['stddev_period']))

        var_res = var_period(self.data['close'], period)
        self.assertTrue(compare_equal(var_res, self.data[period]['var_period']))

        stderr_res = stderr_period(self.data['close'], period)
        self.assertTrue(compare_equal(stderr_res, self.data[period]['stderr_period']))

        min_res = min_period(self.data['close'], period)
        self.assertTrue(compare_equal(min_res, self.data[period]['min_period']))

        max_res = max_period(self.data['close'], period)
        self.assertTrue(compare_equal(max_res, self.data[period]['max_period']))