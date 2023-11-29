"""The TUI Interface."""

import json
import logging
import os
import queue
import time
from typing import Optional

from prompt_toolkit import Application
from prompt_toolkit.application import get_app
from prompt_toolkit.eventloop.inputhook import InputHookContext
from prompt_toolkit.filters import Condition
from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.key_binding import KeyBindings, merge_key_bindings
from prompt_toolkit.layout import (
    ConditionalContainer,
    Float,
    FloatContainer,
    HSplit,
    Layout,
    UIContent,
    UIControl,
    VSplit,
    Window,
)
from prompt_toolkit.styles import Style

from binder_trace import loggers
from binder_trace.parsedParcel import Block
from binder_trace.tui.data_types import DisplayTransaction
from binder_trace.tui.filter import Filter
from binder_trace.tui.frequency_counter import FrequencyCounter
from binder_trace.tui.selection import SelectionViewList
from binder_trace.tui.widget.filters import FiltersPanel
from binder_trace.tui.widget.frequency import FrequencyFrame
from binder_trace.tui.widget.help import HelpPanel
from binder_trace.tui.widget.hexdump import HexdumpFrame
from binder_trace.tui.widget.structure import StructureFrame
from binder_trace.tui.widget.toolbar import StatusToolbar
from binder_trace.tui.widget.transactions import TransactionFrame

CONFIG_FILTERS_KEY = "filters"

log = logging.getLogger(loggers.LOG)


class DummyControl(UIControl):
    """
    A dummy control object that doesn't paint any content.

    Useful for filling a :class:`~prompt_toolkit.layout.Window`. (The
    `fragment` and `char` attributes of the `Window` class can be used to
    define the filling.)
    """

    def create_content(self, width: int, height: int) -> UIContent:
        """Create the dummy control content.

        :param width: Unused.
        :param height: Unused.
        :return: The dummy content.
        """

        def get_line(i: int) -> StyleAndTextTuples:
            return []

        return UIContent(get_line=get_line, line_count=100**100)  # Something very big.

    def is_focusable(self) -> bool:
        """Get the focusable status. (Always true)."""
        return True


class UserInterface:
    """The User Interface encapsulation."""

    def __init__(self, input_queue, pause_unpause, config, config_path):
        """Initialise the user interface.

        :param input_queue: The queue of input to display
        :param pause_unpause: The pause/unpause capture function
        :param config: The configuration to use in the User Interface
        :param config_path: The path to configuration file
        """
        self.filter: Optional[Filter] = None
        self.input_queue = input_queue
        self.all_transactions = []
        self.frequency_counter = FrequencyCounter()
        self.filter_panel = FiltersPanel()
        self.help_panel = HelpPanel()
        self.config_path = config_path
        # TODO: These SVLs should probably be owned by the widgets that control them.
        # This would make it easier to determine heights etc.
        self.transactions = SelectionViewList([], max_view_size=1)
        self.transaction_table = TransactionFrame(self.transactions, self.frequency_counter)
        self.structure_pane = StructureFrame(self.transactions, 1)
        self.hexdump_pane = HexdumpFrame(self.transactions, self.structure_pane.field_selection, 1)
        self.frequency_pane = FrequencyFrame(self.frequency_counter, self.transactions)
        self.pause_unpause = pause_unpause
        self.recording = True
        self.config = None
        self.reload_config()
        self.resize_components(os.get_terminal_size())

    def assign_frequency_filters(self):
        """Assign frequency filters to transactions."""
        self.transactions.assign(
            [
                t
                for t in self.all_transactions
                if self.frequency_counter.check_frequency_filters(t) and self.passes_config_filters(t)
            ]
        )

    def get_recording(self):
        """Get the flag to indicate whether binder transactions are currently being captured.

        :return: The recording status flag.
        """
        return self.recording

    def run(self, inputhook):
        """Start the main TUI."""
        self.focusable = [
            self.transaction_table,
            self.hexdump_pane,
            self.structure_pane,
            self.frequency_pane,
        ]
        self.focus_index = 0
        self.focusable[self.focus_index].activated = True

        kb1 = KeyBindings()

        @kb1.add("s-tab")
        def _(event):
            self.focus_index = (self.focus_index + 1) % len(self.focusable)
            for i, f in enumerate(self.focusable):
                f.activated = i == self.focus_index

        @kb1.add("tab")
        def _(event):
            self.focus_index = len(self.focusable) - 1 if self.focus_index == 0 else self.focus_index - 1
            for i, f in enumerate(self.focusable):
                f.activated = i == self.focus_index

        @kb1.add("C")
        @kb1.add("c")
        def _(event):
            self.transactions.clear()
            self.frequency_counter.svl.clear()

        @kb1.add("space")
        def _(event):
            self.recording = self.pause_unpause()

        dummy_control = DummyControl()
        main_layout = HSplit(
            key_bindings=kb1,
            children=[
                VSplit(
                    [
                        self.transaction_table,
                        self.frequency_pane,
                    ]
                ),
                VSplit(
                    [
                        self.hexdump_pane,
                        self.structure_pane,
                    ]
                ),
                StatusToolbar(self.transactions, self.filter_panel, self.get_recording),
                Window(content=dummy_control),
            ],
        )

        @Condition
        def modal_panel_visible():
            return show_help() or show_filters()

        @Condition
        def show_filters():
            return self.filter_panel.visible

        @Condition
        def show_help():
            return self.help_panel.visible

        layout = Layout(
            container=FloatContainer(
                content=main_layout,
                floats=[
                    Float(
                        top=10,
                        content=ConditionalContainer(content=self.filter_panel, filter=show_filters),
                    ),
                    Float(
                        top=10,
                        content=ConditionalContainer(content=self.help_panel, filter=show_help),
                    ),
                ],
            )
        )
        style = Style(
            [
                ("field.selected", "ansiblack bg:ansiwhite"),
                ("field.default", "fg:ansiwhite"),
                ("frame.label", "fg:ansiwhite"),
                ("frame.border", "fg:ansiwhite"),
                ("frame.border.selected", "fg:ansibrightgreen"),
                ("transaction.heading", "ansiblack bg:ansigray"),
                ("transaction.selected", "ansiblack bg:ansiwhite"),
                ("transaction.default", "fg:ansiwhite"),
                ("transaction.unsupported", "fg:ansibrightblack"),
                ("transaction.error", "fg:#ff6961"),
                ("transaction.no_aidl", "fg:ansiwhite"),
                ("transaction.oneway", "fg:#B69FE4"),
                ("transaction.request", "fg:ansicyan"),
                ("transaction.response", "fg:#FFF880"),
                ("hexdump.default", "fg:ansiwhite"),
                ("hexdump.selected", "fg:ansiblack bg:ansiwhite"),
                ("hexdump.string_length", "fg:ansiblack bg:#bfe3ab"),
                ("hexdump.string_value", "fg:ansiblack bg:#abdbe3"),
                ("hexdump.name", "fg:ansiblack bg:#e3abdb"),
                ("toolbar", "bg:#50818a"),
                ("toolbar.text", "fg:ansiblack"),
                ("dialog", "fg:ansiblack bg:ansiwhite"),
                ("dialog frame.border", "fg:ansiblack bg:ansiwhite"),
                ("dialog frame.label", "fg:ansiblack bg:ansiwhite"),
                ("dialog.textarea", "fg:ansiwhite bg:ansiblack"),
                ("frequency_counter.default", "fg:ansiwhite"),
                ("frequency_counter.interface", "fg:#abdbe3"),
                ("frequency_counter.method", "fg:ansiwhite"),
            ]
        )

        kb = KeyBindings()

        @kb.add("Q", filter=Condition(lambda: not show_filters()))
        @kb.add("q", filter=Condition(lambda: not show_filters()))
        def _(event):
            log.info("Q pressed. App exiting.")
            event.app.exit(exception=KeyboardInterrupt, style="class:aborting")

        @kb.add("H", filter=~modal_panel_visible | show_help)
        @kb.add("h", filter=~modal_panel_visible | show_help)
        @kb.add("enter", filter=show_help)
        def _(event):
            self.help_panel.visible = not self.help_panel.visible

        @kb.add("r")
        @kb.add("R")
        def _(event):
            self.reload_config()

        @kb.add("F", filter=~modal_panel_visible)
        @kb.add("f", filter=~modal_panel_visible)
        @kb.add("enter", filter=show_filters)
        def _(event):
            return
            self.filter_panel.visible = not self.filter_panel.visible
            if self.filter_panel.visible:
                get_app().layout.focus(self.filter_panel.interface_textarea)
            else:
                self.filter = self.filter_panel.filter()

                self.transactions.assign(
                    [t for t in self.all_transactions if self.filter.passes(t) and self.passes_config_filters(t)]
                )

                get_app().layout.focus(dummy_control)

        @kb.add(
            "enter",
            filter=Condition(lambda: self.frequency_pane.activated and not show_filters()),
        )
        def _(event):
            with self.frequency_counter.svl.on_update_event.suspended():
                self.frequency_counter.toggle_filter()

            self.assign_frequency_filters()

        @kb.add("a", filter=Condition(lambda: self.frequency_pane.activated))
        @kb.add("A", filter=Condition(lambda: self.frequency_pane.activated))
        def _(event):
            # Resting the filters to show everything
            self.frequency_counter.filter_all_out(False)
            self.assign_frequency_filters()

        @kb.add("n", filter=Condition(lambda: self.frequency_pane.activated))
        @kb.add("N", filter=Condition(lambda: self.frequency_pane.activated))
        def _(event):
            # Resting the filters to hide everything
            self.frequency_counter.filter_all_out(True)
            self.assign_frequency_filters()

        @kb.add("c-c")
        def _(event):
            active_frame = self.focusable[self.focus_index]
            active_frame.copy_to_clipboard()

        app = Application(
            layout,
            key_bindings=merge_key_bindings(
                [
                    kb,
                    self.transaction_table.key_bindings(),
                    self.structure_pane.key_bindings(),
                    self.hexdump_pane.key_bindings(),
                    self.frequency_pane.key_bindings(),
                ]
            ),
            full_screen=True,
            style=style,
        )
        app.before_render += self.check_resize

        app.run(inputhook=inputhook)

    def reload_frequency_pane(self):
        """Reload the frequency pane."""
        self.frequency_counter.svl.clear()
        for block in self.transactions:
            self.frequency_counter.add_record((block.interface, block.method))

    def reload_config(self) -> list[Filter]:
        """Reload the configuration."""
        if self.config_path:
            if not os.path.exists(self.config_path):
                print("Config path not found.")
                exit(-1)

            with open(self.config_path, "r") as f:
                self.config = json.load(f)

        self.assign_frequency_filters()
        self.reload_frequency_pane()

    def check_resize(self, _):
        """Check the size of components fit with the terminal size and resize if not."""
        new_dimensions = os.get_terminal_size()
        if self.dimensions != new_dimensions:
            self.resize_components(new_dimensions)

    def resize_components(self, dimensions):
        """Resize the components to fit in the given dimensions.

        :param dimensions: The dimensions to git the TUI into.
        """
        self.dimensions = dimensions
        _, height = dimensions

        # Allow for the borders:
        # - top and bottom of transaction frame
        # - top and bottom of lower frames
        # - status bar
        border_allowance = 5
        available_height = height - border_allowance

        # Split into two halfs horizontally. If there are an odd number of lines give the extra to transactions.
        upper_panels_height = available_height - (available_height // 2)
        lower_panels_height = available_height // 2

        self.transaction_table.resize(upper_panels_height)
        self.frequency_pane.resize(upper_panels_height)
        self.structure_pane.max_height = lower_panels_height
        self.hexdump_pane.max_lines = lower_panels_height

    def get_available_blocks(self):
        """Get the next 10 transactio blocks to visualise."""
        blocks: list[Block] = []
        # Retrieve every unhandled block currently available in the queue
        try:
            for _ in range(10):
                blocks.append(self.input_queue.get_nowait())
        except queue.Empty:
            pass
        return blocks

    def passes_config_filters(self, block: DisplayTransaction) -> bool:
        """Check a given transaction block passes all active filters."""
        allowed = True
        filters = []

        if self.config:
            for filter in self.config[CONFIG_FILTERS_KEY]:
                tmp_filter = Filter()
                tmp_filter.from_json(filter)
                filters.append(tmp_filter)

            for filter in filters:
                filter_pass = filter.passes(block)
                # Inclusive=True takes precedence over excludes
                if filter_pass and filter.inclusive:
                    allowed = True
                    break
                else:
                    allowed = allowed & filter_pass

        return allowed

    def process_data(self):
        """Process the current tranche of transaction blocks."""
        blocks = self.get_available_blocks()
        # For every block...
        for block in blocks:
            block = DisplayTransaction(block)
            if (
                self.passes_config_filters(block)
                and ((not self.filter) or self.filter.passes(block))
                and self.frequency_counter.check_frequency_filters(block)
            ):
                self.transactions.append(block)
                self.frequency_counter.add_record((block.interface, block.method))

            self.all_transactions.append(block)

        return bool(blocks)


def start_ui(block_queue: queue.Queue, pause_unpause, config, config_path):
    """
    Start and run the TUI, with the main event loop.

    args:
        message_queue:
        block_queue:
    """
    # Create the UIDisplay with a given display filter
    ui = UserInterface(block_queue, pause_unpause, config, config_path)

    def inputhook(inputhook_context: InputHookContext):
        while not inputhook_context.input_is_ready():
            if ui.process_data():
                get_app().invalidate()
            else:
                time.sleep(0.1)

    ui.run(inputhook)
