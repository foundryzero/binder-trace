"""Parcel tests."""
import unittest

from binder_trace.parseerror import ParseError


class TestParcel(unittest.TestCase):
    """Parcel tests."""

    def test_simple(self) -> None:
        """A simple test of ParseError's initialisation."""
        token = ParseError("err")
        self.assertEqual(token.message, "err")
