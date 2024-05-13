"""Data types for TUI."""

import datetime
from typing import Optional

from binder_trace.parsedParcel import Block, Direction, Field


class DisplayTransaction:
    """Display Transaction type."""

    def __init__(self, block: Block) -> None:
        """Initialise DisplayTransaction."""
        if not block or not block.root_field:
            raise ValueError("no block")

        self.block: Block = block
        self.timestamp = (datetime.datetime.now().strftime("%H:%M:%S"),)

    @property
    def unsupported_call(self) -> bool:
        """Get unsupported call property."""
        return self.block.unsupported_call

    @property
    def interface(self) -> str:
        """Get interface name property."""
        return self.block.interface_name

    @property
    def method_number(self) -> int:
        """Get method number property."""
        return self.block.code

    @property
    def method(self) -> str:
        """Get call name property."""
        return self.block.call_name

    @property
    def raw_data(self) -> bytes:
        """Get raw data property."""
        return self.block.raw_data

    @property
    def fields(self) -> Optional[Field]:
        """Get fields property."""
        return self.block.root_field

    @property
    def direction_indicator(self) -> str:
        """Get direction indicator property."""
        if self.block.direction == Direction.IN:
            return "\u21D0" if self.block.oneway else "\u21D2"
        elif self.block.direction == Direction.OUT:
            return "\u21CF"
        else:
            return ""

    def style(self) -> str:
        """Get type name."""
        if self.unsupported_call:
            style = "class:transaction.unsupported"
        elif self.block.errors:
            style = "class:transaction.error"
        elif self.block.unsupported_call:
            style = "class:transaction.no_aidl"
        elif self.block.direction == Direction.IN:
            style = "class:transaction.oneway" if self.block.oneway else "class:transaction.request"
        elif self.block.direction == Direction.OUT:
            style = "class:transaction.response"
        else:
            style = "class:transaction.default"
        return style

    def type(self) -> str:
        """Get the type of the Block as a simple short string for use in pattern matching."""
        if self.unsupported_call:
            type_name = "unsupported type"
        elif self.block.errors:
            type_name = "error"
        elif self.block.direction == Direction.IN:
            # TODO: Should this be "oneway" or "async call"?
            type_name = "oneway" if self.block.oneway else "call"
        elif self.block.direction == Direction.OUT:
            type_name = "return"
        else:
            type_name = "unknown"  # Should be impossible

        return type_name
