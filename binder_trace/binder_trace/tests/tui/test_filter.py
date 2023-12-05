import unittest

from binder_trace.parsedParcel import Block, Field
from binder_trace.tui.data_types import DisplayTransaction
from binder_trace.tui.filter import Filter, FilterSet


class TestFilter(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def create_transaction(self, interface=None, method=None):
        return DisplayTransaction(
            Block(
                interface_name=interface,
                call_name=method,
                raw_data=b"",
                code=0,
                oneway=False,
                direction=None,
                root_field=Field("", []),
            )
        )

    def test_interface_filter(self):
        filter = Filter(interface="com.android")
        self.assertFalse(filter.passes(self.create_transaction(interface="com.google.something")))
        self.assertTrue(filter.passes(self.create_transaction(interface="com.android.something")))

    def test_exlude_interface_filter(self):
        filter = Filter(interface="com.android", include=False)
        self.assertTrue(filter.passes(self.create_transaction(interface="com.google.something")))
        self.assertFalse(filter.passes(self.create_transaction(interface="com.android.something")))

    def test_toggle_inclusivity(self):
        filter = Filter(interface="com.android")
        filter.toggle_inclusivity()
        self.assertTrue(filter.passes(self.create_transaction(interface="com.google.something")))

    def test_method_filter(self):
        filter = Filter(method="some_method")
        self.assertFalse(filter.passes(self.create_transaction(method="some_other")))
        self.assertTrue(filter.passes(self.create_transaction(method="some_method")))


class TestFilterSet(unittest.TestCase):
    def test_passes_returns_true_for_empty_set(self):
        filters = FilterSet()
        self.assertTrue(filters.passes("anything"))
