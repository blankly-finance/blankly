"""
    Indicator tests
    Copyright (C) 2021  Emerson Dove

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""


import pickle
import unittest
from pathlib import Path

import numpy as np

from blankly.indicators import ema, hma, kaufman_adaptive_ma, macd, sma, trima, vwma, wma, zlema


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