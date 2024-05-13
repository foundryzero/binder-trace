"""Frequency frame UI."""

import csv
import io
import logging
from typing import Any

import pyperclip

# Importing necessary modules and classes
from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import AnyContainer, Dimension
from prompt_toolkit.widgets import Label

# Importing additional modules and classes from the binder_trace package
from binder_trace import loggers
from binder_trace.tui import table
from binder_trace.tui.data_types import DisplayTransaction
from binder_trace.tui.frequency_counter import FilterType, FrequencyCounter, FrequencyRecord
from binder_trace.tui.selection import SelectionViewList
from binder_trace.tui.widget.frame import SelectableFrame

log = logging.getLogger(loggers.LOG)


# Define a class named FrequencyFrame
class FrequencyFrame:
    """FrequencyFrame UI element."""

    def __init__(self, frequency_counter: FrequencyCounter, transactions: SelectionViewList[Any]):
        """Initialise FrequencyFrame.

        :param frequency_counter: Counter helper
        :param transactions: SelectionViewList of transactions
        """
        self.transactions = transactions
        self.frequency_counter = frequency_counter
        self.frequency_counter.svl.on_update_event += self.update_table
        self.cache = None

        # Headings for the frequency frame
        self.headings = [
            Label("Interface/Method"),
            Label("Frequency"),
            Label("Filter"),
        ]

        # Defining the table where the frequency data will be displayed
        self.table = table.Table(
            table=[self.headings],
            column_width=Dimension.exact(10),
            column_widths=[
                Dimension(min=25, preferred=40),
                Dimension(min=4, preferred=11, max=11),
                Dimension(min=4, preferred=8, max=8),
            ],
            borders=table.EmptyBorder,
        )
        self.direction = 0

        self.pad_table()

        # Create an instance of SelectableFrame with a title and dimensions
        self.container = SelectableFrame(
            title="Frequency",
            body=self.get_content,
            width=Dimension(preferred=60, max=70),
        )

    def resize(self, height: int) -> None:
        """Resize the header row.

        :param height: The height to resize.
        """
        # Subtract one for the header row
        height -= 1
        self.frequency_counter.svl.resize_view(height)

    # Define a method to get the content of the FrequencyFrame
    def get_content(self) -> table.Table:
        """Get the content of the FrequencyFrame.

        :return: FrequencyFrame table
        """
        return self.table

    def jump_interface_selection(self, reverse: bool) -> None:
        """Move selection within the interface.

        :param reverse: Whether the direction should be reversed.
        """
        # Store the current selection in a variable for comparison later
        self.selection = self.frequency_counter.svl[self.frequency_counter.svl.selection]

        # Find the indices that match the filter criteria
        indices = [i for i, x in enumerate(self.transactions) if self.matches_selection(x)]

        if not indices:
            # No matching transactions found, reset the direction and return
            self.direction = 0
            return

        # If the selection has changed, reset the direction
        if self.selection != self.cache:
            self.direction = 0
        else:
            if reverse:
                # Decrement the direction
                self.direction = len(indices) - 1 if self.direction <= 0 else self.direction - 1
            else:
                # Increment the direction
                self.direction = 0 if self.direction >= len(indices) - 1 else self.direction + 1

        # Update the selection and cache
        self.transactions.move_selection(indices[self.direction] - self.transactions.selection)
        self.transactions.selection = indices[self.direction]
        self.cache = self.selection

    def matches_selection(self, transaction: DisplayTransaction) -> bool:
        """Check if a transaction matches the selected filter.

        :param transaction: The transaction to check against the filter.
        :return: True if the transaction matches the filter (taking INCLUDE / EXCLUDE mode into account)
        """
        result: bool = False
        if self.selection.filter == FilterType.INCLUDE and self.selection.interface == transaction.interface:
            if self.selection.method:
                result = transaction.method == self.selection.method
            else:
                result = True
        return result

    def update_table(self, _) -> None:
        """Update the frequency table.

        :param _: Unused
        """
        self.table.children.clear()
        self.table.add_row(self.headings, "class:frequency_counter.heading", id(self.headings))
        # Only showing the part of the selection view list that can be seen on the UI
        for i in range(
            self.frequency_counter.svl.view.start,
            self.frequency_counter.svl.view.end,
        ):
            row, style = self._to_row(self.frequency_counter.svl[i])
            self.table.add_row(
                row,
                f"{style} reverse" if i == self.frequency_counter.svl.selection else style,
                (
                    hash(self.frequency_counter.svl[i]),
                    i == self.frequency_counter.svl.selection,
                ),
            )
        self.pad_table()

    def pad_table(self) -> None:
        """Pad the table."""
        padding = self.frequency_counter.svl.max_view_size - self.frequency_counter.svl.view.size()
        empty_row = [
            Label(""),
            Label(""),
            Label(""),
        ]
        for _ in range(padding):
            self.table.add_row(empty_row, "class:frequency_counter.default", id(empty_row))

    def key_bindings(self) -> KeyBindings:
        """Key bindings."""
        kb = KeyBindings()

        @kb.add("up", filter=Condition(lambda: self.activated))
        def _(event):
            self.frequency_counter.svl.move_selection(-1)

        @kb.add("down", filter=Condition(lambda: self.activated))
        def _(event):
            self.frequency_counter.svl.move_selection(1)

        @kb.add("s-up", filter=Condition(lambda: self.activated))
        def _(event):
            self.frequency_counter.svl.move_selection(-self.frequency_counter.svl.max_view_size)

        @kb.add("s-down", filter=Condition(lambda: self.activated))
        def _(event):
            self.frequency_counter.svl.move_selection(self.frequency_counter.svl.max_view_size)

        @kb.add("home", filter=Condition(lambda: self.activated))
        def _(event):
            self.frequency_counter.svl.move_selection(-self.frequency_counter.svl.selection)

        @kb.add("end", filter=Condition(lambda: self.activated))
        def _(event):
            self.frequency_counter.svl.move_selection(
                len(self.frequency_counter.svl) - self.frequency_counter.svl.selection
            )

        @kb.add("p", filter=Condition(lambda: self.activated))
        @kb.add("P", filter=Condition(lambda: self.activated))
        def _(event):
            # Reversing the order of thelist based on frequency vaules
            self.frequency_counter.toggle_sort()

        @kb.add("w", filter=Condition(lambda: self.activated))
        @kb.add("W", filter=Condition(lambda: self.activated))
        def _(event):
            # Reversing the order of thelist based on frequency vaules
            self.jump_interface_selection(False)

        @kb.add("s", filter=Condition(lambda: self.activated))
        @kb.add("S", filter=Condition(lambda: self.activated))
        def _(event):
            # Reversing the order of thelist based on frequency vaules
            self.jump_interface_selection(True)

        return kb

    def copy_to_clipboard(self):
        """Key bindings."""
        if self.frequency_counter.svl.selection_valid():
            output = io.StringIO()
            writer = csv.writer(output, quoting=csv.QUOTE_NONE)
            for i in range(len(self.frequency_counter.svl)):
                t = self.frequency_counter.svl[i]
                writer.writerow([t.interface, t.method, t.frequency, t.filter])
            pyperclip.copy(output.getvalue())

    def _to_row(self, selection: FrequencyRecord):
        """Create a row from a transaction.

        :param transaction: The transaction
        :return: The row
        """
        # TODO: Cache the rows so we don't need to recreate them.
        # Checking which style to use for the interface and method
        if not selection.method:
            label = selection.interface
            style = "class:frequency_counter.interface"
        else:
            label = f"   {selection.method}"
            style = "class:frequency_counter.method"
        # Returning the interface or method, frequency, filter with its value and the style of the row
        return [
            Label(label),
            Label(str(selection.frequency)),
            Label("[-]" if selection.filter == FilterType.EXCLUDE else "[+]"),
        ], style

    # Define a property 'activated' to get the activation status of the container
    @property
    def activated(self) -> bool:
        """Get activated flag."""
        return self.container.activated

    # Define a setter for the 'activated' property
    @activated.setter
    def activated(self, value: bool):
        """Set activated flag.

        :param value: Flag value
        """
        self.container.activated = value

    def max_data_line_count(self):
        """Get maximum number of lines for frame."""
        return len(self.frequency_counter.svl)

    # Define a special method to return the container
    def __pt_container__(self) -> AnyContainer:
        """Get internal container."""
        return self.container
