"""Toolbar pane."""

from typing import Any, Callable, Sequence

from prompt_toolkit.formatted_text import AnyFormattedText, FormattedText
from prompt_toolkit.layout.containers import AnyContainer, DynamicContainer
from prompt_toolkit.widgets import FormattedTextToolbar

from binder_trace.tui.widget.filters import FiltersPanel


class StatusToolbar:
    """The status toolbar."""

    def __init__(self, transactions: Sequence[Any], filters: FiltersPanel, recording: Callable[[], bool]) -> None:
        """Initialise the toolbar.

        :param transactions: The transactions
        :param filters: The filters
        :param recording: Flag for whether recording is occuring
        """
        self.transactions = transactions
        self.filters = filters
        self.container = DynamicContainer(self.toolbar_container)
        self.recording = recording

    def toolbar_container(self) -> AnyContainer:
        """Get the toolbar container.

        :return: The toolbar
        """
        return FormattedTextToolbar(
            text=self.toolbar_text(),
            style="class:toolbar",
        )

    def toolbar_text(self) -> AnyFormattedText:
        """Generate the toolbar text."""
        return FormattedText(
            [
                (
                    "class:toolbar.text",
                    (
                        f"Transactions: {len(self.transactions)}, "
                        f"Filter: [{self.filters.filter()}] Recording: {str(self.recording())}"
                    ),
                )
            ]
        )

    def __pt_container__(self) -> AnyContainer:
        """Get the internal container.

        :return: The container
        """
        return self.container
