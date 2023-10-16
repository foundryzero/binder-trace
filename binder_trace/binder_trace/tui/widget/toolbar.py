from typing import Sequence

from prompt_toolkit.formatted_text import AnyFormattedText, FormattedText
from prompt_toolkit.layout.containers import AnyContainer, DynamicContainer
from prompt_toolkit.widgets import FormattedTextToolbar

from binder_trace.tui.widget.filters import FiltersPanel


class StatusToolbar:
    def __init__(self, transactions: Sequence, filters: FiltersPanel, recording) -> None:
        self.transactions = transactions
        self.filters = filters
        self.container = DynamicContainer(self.toolbar_container)
        self.recording = recording

    def toolbar_container(self) -> AnyContainer:
        return FormattedTextToolbar(
            text=self.toolbar_text(),
            style="class:toolbar",
        )

    def toolbar_text(self) -> AnyFormattedText:
        return FormattedText(
            [
                (
                    "class:toolbar.text",
                    f"Transactions: {len(self.transactions)}, Filter: [{self.filters.filter()}] Recording: {str(self.recording())}",
                )
            ]
        )

    def __pt_container__(self) -> AnyContainer:
        return self.container
