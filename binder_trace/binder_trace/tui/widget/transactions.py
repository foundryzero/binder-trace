import csv
import io

import pyperclip
from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import AnyContainer
from prompt_toolkit.layout.dimension import AnyDimension, Dimension

from binder_trace.tui import table
from binder_trace.tui.selection import SelectionViewList
from binder_trace.tui.widget.frame import SelectableFrame


class TransactionFrame:
    def __init__(
        self,
        transactions: SelectionViewList,
        frequency_counter: SelectionViewList,
        height: AnyDimension = None,
    ) -> None:
        self.transactions = transactions
        self.frequency_counter = frequency_counter
        self.transactions.on_update_event += self.update_table

        self.headings = [
            table.Label(""),
            table.Label("Interface"),
            table.Label("#"),
            table.Label("Method"),
            table.Label("len"),
            table.Label(""),
        ]

        self.table = table.Table(
            table=[self.headings],
            # height=height,
            column_width=Dimension.exact(10),
            column_widths=[
                Dimension.exact(1),
                Dimension(min=20, preferred=40),
                Dimension(min=2, preferred=4, max=4),
                Dimension(min=10, preferred=30),
                Dimension.exact(6),
                Dimension(preferred=100),
            ],
            borders=table.EmptyBorder,
        )

        self.pad_table()

        self.container = SelectableFrame(
            title="Transactions",
            body=self.get_content,
        )

    def resize(self, height):
        # Subtract one for the header row
        height -= 1
        self.transactions.resize_view(height)

    def get_content(self):
        return self.table

    def update_table(self, _):
        self.table.children.clear()

        self.table.add_row(self.headings, "class:transactions.heading", id(self.headings))
        for i in range(self.transactions.view.start, self.transactions.view.end):
            row, style = self._to_row(self.transactions[i])
            self.table.add_row(
                row,
                f"{style} reverse" if i == self.transactions.selection else style,
                (id(self.transactions[i]), i == self.transactions.selection),
            )

        self.pad_table()

    def pad_table(self):
        padding = self.transactions.max_view_size - self.transactions.view.size()
        empty_row = [
            table.Label(""),
            table.Label(""),
            table.Label(""),
            table.Label(""),
            table.Label(""),
            table.Label(""),
        ]
        for _ in range(padding):
            self.table.add_row(empty_row, "class:transaction.default", id(empty_row))

    def key_bindings(self) -> KeyBindings:
        kb = KeyBindings()

        @kb.add("up", filter=Condition(lambda: self.activated))
        def _(event):
            self.transactions.move_selection(-1)

        @kb.add("down", filter=Condition(lambda: self.activated))
        def _(event):
            self.transactions.move_selection(1)

        @kb.add("s-up", filter=Condition(lambda: self.activated))
        def _(event):
            self.transactions.move_selection(-self.transactions.max_view_size)

        @kb.add("s-down", filter=Condition(lambda: self.activated))
        def _(event):
            self.transactions.move_selection(self.transactions.max_view_size)

        @kb.add("home", filter=Condition(lambda: self.activated))
        def _(event):
            self.transactions.move_selection(-self.transactions.selection)

        @kb.add("end", filter=Condition(lambda: self.activated))
        def _(event):
            self.transactions.move_selection(len(self.transactions) - self.transactions.selection)

        return kb

    @property
    def activated(self):
        return self.container.activated

    # Define a "name" setter
    @activated.setter
    def activated(self, value):
        self.container.activated = value

    def copy_to_clipboard(self):
        if self.transactions.selection_valid():
            output = io.StringIO()
            writer = csv.writer(output, quoting=csv.QUOTE_NONE)
            for t in self.transactions.data:
                writer.writerow([t.interface, str(t.method_number), t.method, hex(len(t.raw_data))])
            pyperclip.copy(output.getvalue())

    def _to_row(self, transaction):
        # TODO: Cache the rows so we don't need to recreate them.
        return [
            table.Label(transaction.direction_indicator),
            table.Label(transaction.interface),
            table.Label(str(transaction.method_number)),
            table.Label(transaction.method),
            table.Label(hex(len(transaction.raw_data))),
            table.Label(""),
        ], transaction.style()

    def __pt_container__(self) -> AnyContainer:
        return self.container
