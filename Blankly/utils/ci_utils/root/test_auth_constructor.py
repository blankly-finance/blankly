import unittest
import Blankly.auth_constructor as auth


class TestAuthConstructor(unittest.TestCase):
    def test_to_upper(self):
        output = auth.to_upper('input')
        self.assertEqual(output, 'INPUT')
