"""Hexdump Pane."""

from typing import Optional

import hexdump
import pyperclip
from prompt_toolkit.filters import Condition
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import AnyContainer, Dimension, FormattedTextControl, HSplit, Window

from binder_trace.tui import listing
from binder_trace.tui.data_types import DisplayTransaction
from binder_trace.tui.selection import SelectionViewList
from binder_trace.tui.widget.frame import SelectableFrame


class HexdumpFrame:
    """The hexdump frame."""

    def __init__(self, transactions: SelectionViewList, fields: SelectionViewList, max_lines: int) -> None:
        """Intiailise HexdumpFrame.

        :param transactions: Transactions.
        :param fields: Fields
        :param max_lines: Maximum number of lines to display
        """
        self.transactions = transactions
        self.fields = fields
        self.max_lines = max_lines

        self.transactions.on_selection_change += self.update_content
        self.fields.on_selection_change += self.update_content_and_jump_to_selection

        self.offset = 0

        self.container = SelectableFrame(
            title="Hexdump",
            body=self.get_content,
            width=Dimension(min=56, preferred=76, max=76),
            height=Dimension(preferred=max_lines),
        )

    def key_bindings(self) -> KeyBindings:
        """Key bindings."""
        kb = KeyBindings()

        @kb.add("up", filter=Condition(lambda: self.activated))
        def _(event):
            if self.transactions.selection_valid():
                self.offset = max(0, self.offset - 1)

        @kb.add("down", filter=Condition(lambda: self.activated))
        def _(event):
            if self.transactions.selection_valid():
                if self.offset + self.max_lines + 1 <= self.max_data_line_count():
                    self.offset += 1

        @kb.add("s-up", filter=Condition(lambda: self.activated))
        def _(event):
            if self.transactions.selection_valid():
                self.offset = max(0, self.offset - self.max_lines)

        @kb.add("s-down", filter=Condition(lambda: self.activated))
        def _(event):
            if self.transactions.selection_valid():
                self.offset = min(
                    self.offset + self.max_lines,
                    self.max_data_line_count() - self.max_lines,
                )

        @kb.add("home", filter=Condition(lambda: self.activated))
        def _(event):
            if self.transactions.selection_valid():
                self.offset = 0

        @kb.add("end", filter=Condition(lambda: self.activated))
        def _(event):
            if self.transactions.selection_valid():
                data_len = len(self.transactions.selected().raw_data)
                max_data_lines = data_len // 16 + 1
                self.offset = max_data_lines - self.max_lines

        return kb

    @property
    def activated(self) -> bool:
        """Get activated flag."""
        return self.container.activated

    @activated.setter
    def activated(self, value: bool):
        """Set activated flag.

        :param value: Flag value
        """
        self.container.activated = value

    def copy_to_clipboard(self):
        """Copy selected transaction text to the clipboard."""
        if self.transactions.selection_valid():
            pyperclip.copy(hexdump.hexdump(self.transactions.selected().raw_data, "return"))

    def max_data_line_count(self):
        """Get the maxmium number of lines that will fit in the frame."""
        data_len = len(self.transactions.selected().raw_data)
        return data_len // 16 + 1

    def update_content(self, _, offset=0):
        """Update frame content."""
        self.offset = offset
        self.container.body = self.get_content()

    def update_content_and_jump_to_selection(self, _):
        """Update the hexdump content and jumps the select to the selected location."""
        position = self.selected_field_position()
        offset = 0
        if position:
            # Set the offset to the first line containing the selected field
            start = position.start // 16
            end = position.end // 16

            if end - offset > self.max_lines:
                # The field is too big to fit so just show as much as possible
                offset = start
            elif start >= self.offset and end <= self.offset + self.max_lines:
                # Do nothing its already in view
                offset = self.offset
            elif start < self.offset:
                # Scroll up to the field
                offset = start
            else:
                offset = self.offset + (end - self.offset + self.max_lines)

        self.update_content(_, offset)

    def get_content(self) -> AnyContainer:
        """Get the content of the hexdump."""
        return HSplit(
            children=[
                Window(
                    ignore_content_height=True,
                    content=FormattedTextControl(
                        text=self.to_hexdump(
                            self.transactions.selected() if self.transactions.selection_valid() else None
                        )
                    ),
                ),
            ]
        )

    def selected_field_position(self):
        """Get the position that is selected."""
        return self.fields.selected().field.field.position or None if self.fields.selection_valid() else None

    def to_hexdump(self, transaction: Optional[DisplayTransaction]) -> FormattedText:
        """Generate the hexdump from the transaction.

        :param transaction: The transaction to dump
        :return: The hexdump text.
        """
        position = self.selected_field_position()
        selection = self.fields.selected().field.position() if position else []

        return listing.to_hexdump(
            transaction.raw_data if transaction else b"",
            "class:hexdump.default",
            selection,
            offset=self.offset * 16,
        )

    def __pt_container__(self) -> AnyContainer:
        """Get internal container."""
        return self.container
