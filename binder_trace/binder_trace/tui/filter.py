import json
from collections import UserList
from typing import Optional, TypeVar

from binder_trace.tui.data_types import DisplayTransaction

INTERFACE_KEY = "interface"
METHOD_KEY = "method"
TYPE_KEY = "type"
INCLUSIVE_KEY = "inclusive"


class Filter:
    """
    CLASS Filter
        Brief - Class that represents a single filter
        Description -
            It holds and interface, method and list of types to check against
            It also holds the function which checks if a block passes the filter
    """

    def __init__(
        self,
        interface: Optional[str] = None,
        method: Optional[str] = None,
        types: Optional[list[str]] = None,
        include: bool = True,
    ):
        self.interface = interface
        self.method = method
        self.types = types or []  # List of associated types of the filter (call, return, etc)
        self.inclusive = include

    def passes(self, block: DisplayTransaction):
        """
        FUNCTION passes
            Brief - Returns whether a block should be displayed
            Description -
                Returns TRUE if the block should be shown
                Returns FALSE if the block should no be shown

                The code checks if the filter passes the checks, and then tailors the output to the filter_mode
                The type is either Inclusive ("Incl") or Exclusive ("Excl")
        """
        matches = (
            (not self.types or block.type() in self.types)
            and (not self.interface or self.interface in block.interface)
            and (not self.method or self.method in block.method)
        )
        return not matches ^ self.inclusive

    def toggle_inclusivity(self):
        self.inclusive = not self.inclusive

    def __str__(self):
        interface = self.interface or "*"
        method = self.method or "*"
        types = "|".join(self.types) if self.types else "*"

        return f"interface={interface}, method={method}, types={types}, inclusive={self.inclusive}"

    def to_json(self):
        return json.dumps(
            {
                INTERFACE_KEY: self.interface or "",
                METHOD_KEY: self.method or "",
                TYPE_KEY: "|".join(self.types) if self.types else "",
                INCLUSIVE_KEY: self.inclusive,
            }
        )

    def from_json(self, json_filter):
        self.interface = json_filter.get(INTERFACE_KEY)
        self.method = json_filter.get(METHOD_KEY)
        self.inclusive = json_filter.get(INCLUSIVE_KEY, True)
        self.types = [k for k in json_filter.get(TYPE_KEY, "").split("|") if k] or None


_T = TypeVar("_T", bound=Filter)


class FilterSet(UserList[_T]):
    def passes(self, interface=None, method=None, call_type=None):
        """Return True if all filters in the set pass, False otherwise."""
        return all([f.passes(interface, method, call_type) for f in self.data])
