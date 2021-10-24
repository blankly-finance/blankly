import pickle
import unittest
from pathlib import Path

import numpy as np

from blankly.metrics import *

class Metrics(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.start_value = 100
        cls.end_value = 150
        cls.years = 2
        cls.returns = [0.03, 0.05, -0.06, -0.02, 0.03, 0.025, 0.5, 0]

    def test_cagr(self):
        truth = 0.2247448714
        result = cagr(self.start_value, self.end_value, self.years)
        self.assertAlmostEqual(truth, result)
    
    def test_cum_returns(self):
        value = cum_returns(self.start_value, self.end_value)
        self.assertEqual(0.5, value)
    
    def test_sortino(self):
        truth = 38.93662218111633
        result = sortino(self.returns)
        self.assertEqual(truth, result)

    def test_sharpe(self):
        truth = 6.206188187237863
        result = sharpe(self.returns)
        self.assertEqual(truth, result)

    def test_maxdrawdown(self):
        truth = -0.07880
        result = max_drawdown(self.returns)
        self.assertAlmostEqual(truth, result)