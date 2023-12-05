import unittest

from binder_trace.parsedParcel import FieldData


class FieldDataTest(unittest.TestCase):
    def test_equality_is_equal(self):
        a = FieldData(10, 100)
        b = FieldData(10, 100)

        self.assertEqual(a, b)

    def test_equality_not_equal(self):
        a = FieldData(10, 100)
        b = FieldData(10, 200)

        self.assertNotEqual(a, b)
