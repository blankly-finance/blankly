"""
    Oscillator tests
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

from blankly.indicators import absolute_price_oscillator, aroon_oscillator, chande_momentum_oscillator, \
    percentage_price_oscillator, rsi, stochastic_oscillator


def compare_equal(a, b):
    # compares two numpy arrays
    return np.array_equal(a, b)


class Oscillators(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        data_path = Path("tests/config/test_data.p").resolve()
        with open(data_path, 'rb') as f:
            cls.data = pickle.load(f)

    def test_rsi(self):
        for period in self.data['periods']:
            rsi_res = rsi(self.data['close'], period)
            self.assertTrue(compare_equal(rsi_res, self.data[period]['rsi']))

    def test_aroon_oscillator(self):
        for period in self.data['periods']:
            aroon_res = aroon_oscillator(self.data['high'], self.data['low'], period)
            self.assertTrue(compare_equal(aroon_res, self.data[period]['aroon_oscillator']))

    def test_chande_momentum_oscillator(self):
        for period in self.data['periods']:
            chande_res = chande_momentum_oscillator(self.data['close'], period)
            self.assertTrue(compare_equal(chande_res, self.data[period]['chande_momentum_oscillator']))


    def test_absolute_price_oscillator(self):
        short_period = self.data['short_period']
        long_period = self.data['long_period']
        res = absolute_price_oscillator(self.data['close'], short_period, long_period)
        # use the first one since general period doesn't matter
        self.assertTrue(compare_equal(res, self.data[self.data['periods'][0]]['absolute_price_oscillator']))

    def test_percentage_price_oscillator(self):
        short_period = self.data['short_period']
        long_period = self.data['long_period']
        res = percentage_price_oscillator(self.data['close'], short_period, long_period)
        # use the first one since general period doesn't matter
        self.assertTrue(compare_equal(res, self.data[self.data['periods'][0]]['percentage_price_oscillator']))

    def test_stochastic_oscillator(self):
        pct_k_period = self.data['pct_k_period']
        pct_k_slowing_period = self.data['pct_k_slowing_period']
        pct_d_period = self.data['pct_d_period']
        res = stochastic_oscillator(self.data['high'], self.data['low'], self.data['close'], pct_k_period, pct_k_slowing_period, pct_d_period)
        # use the first one since general period doesn't matter
        self.assertTrue(compare_equal(res, self.data[self.data['periods'][0]]['stochastic_oscillator']))