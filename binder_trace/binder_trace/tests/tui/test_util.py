import unittest

from binder_trace.tui.util import clamp


class TestClamp(unittest.TestCase):
    def test_clamp_within_range(self):
        self.assertEqual(3, clamp(1, 4, 3))

    def test_clamp_below_range(self):
        self.assertEqual(1, clamp(1, 4, 0))

    def test_clamp_above_range(self):
        self.assertEqual(4, clamp(1, 4, 5))
