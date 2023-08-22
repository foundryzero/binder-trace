
import logging
import os
import queue
from typing import Optional

from prompt_toolkit import Application
from prompt_toolkit.application import get_app
from prompt_toolkit.filters import Condition
from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.layout import HSplit, Layout, VSplit, Window, FloatContainer, Float, ConditionalContainer, UIControl, UIContent
from prompt_toolkit.key_binding import KeyBindings, merge_key_bindings
from prompt_toolkit.styles import Style

from binder_trace import loggers
from binder_trace.parsedParcel import Block
from binder_trace.tui.filter import Filter
from binder_trace.tui.selection import SelectionViewList
from binder_trace.tui.data_types import DisplayTransaction
from binder_trace.tui.widget.toolbar import StatusToolbar
from binder_trace.tui.widget.filters import FiltersPanel
from binder_trace.tui.widget.help import HelpPanel
from binder_trace.tui.widget.hexdump import HexdumpFrame
from binder_trace.tui.widget.structure import StructureFrame
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
        def get_line(i: int) -> StyleAndTextTuples:
            return []

        return UIContent(
            get_line=get_line, line_count=100**100
        )  # Something very big.

    def is_focusable(self) -> bool:
        return True

class UserInterface:

    def __init__(self, input_queue, pause_unpause, config):
        self.filter: Optional[Filter] = None
        self.input_queue = input_queue

        self.all_transactions = []

        self.filter_panel = FiltersPanel()
        self.help_panel = HelpPanel()

        # TODO: These SVLs should probably be owned by the widgets that control them. This would make it easier to determine heights etc.
        self.transactions = SelectionViewList([], max_view_size=1)
        self.transaction_table = TransactionFrame(self.transactions)
        self.structure_pane = StructureFrame(self.transactions, 1)
        self.hexdump_pane = HexdumpFrame(self.transactions, self.structure_pane.field_selection, 1)

        self.pause_unpause = pause_unpause
        self.recording = True

        self.config = config

        self.resize_components(os.get_terminal_size())

    def get_recording(self):
        return self.recording

    def run(self):
        self.focusable = [self.transaction_table, self.hexdump_pane, self.structure_pane]
        self.focus_index = 0
        self.focusable[self.focus_index].activated = True

        kb1 = KeyBindings()

        @kb1.add('tab')
        def _(event):
            self.focus_index = (self.focus_index + 1) % len(self.focusable)
            for i, f in enumerate(self.focusable):
                f.activated = i == self.focus_index

        @kb1.add('s-tab')
        def _(event):
            self.focus_index = len(self.focusable) - 1 if self.focus_index == 0 else self.focus_index -1
            for i, f in enumerate(self.focusable):
                f.activated = i == self.focus_index

        @kb1.add('C')
        @kb1.add('c')
        def _(event):
            self.transactions.clear()

        @kb1.add('space')
        def _(event):
            self.recording = self.pause_unpause()

        dummy_control = DummyControl()
        main_layout = HSplit(
            key_bindings=kb1,
            children=[
                self.transaction_table,
                VSplit([
                    self.hexdump_pane,
                    self.structure_pane,
                ]),
                StatusToolbar(self.transactions, self.filter_panel, self.get_recording),
                Window(content=dummy_control)
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
                    Float(top=10, content=ConditionalContainer(content=self.filter_panel, filter=show_filters)),
                    Float(top=10, content=ConditionalContainer(content=self.help_panel, filter=show_help)),
                ]
            )
        )

        style = Style([
            ('field.selected', 'ansiblack bg:ansiwhite'),
            ('field.default', 'fg:ansiwhite'),
            ('frame.label', 'fg:ansiwhite'),
            ('frame.border', 'fg:ansiwhite'),
            ('frame.border.selected', 'fg:ansibrightgreen'),
            ('transaction.heading', 'ansiblack bg:ansigray'),
            ('transaction.selected', 'ansiblack bg:ansiwhite'),
            ('transaction.default', 'fg:ansiwhite'),
            ('transaction.unsupported', 'fg:ansibrightblack'),
            ('transaction.error', 'fg:ansired'),
            ('transaction.no_aidl', 'fg:ansiwhite'),
            ('transaction.oneway', 'fg:ansimagenta'),
            ('transaction.request', 'fg:ansicyan'),
            ('transaction.response', 'fg:ansiyellow'),
            ('hexdump.default', 'fg:ansiwhite'),
            ('hexdump.selected', 'fg:ansiblack bg:ansiwhite'),
            ('toolbar', 'bg:ansigreen'),
            ('toolbar.text', 'fg:ansiblack'),
            ('dialog', 'fg:ansiblack bg:ansiwhite'),
            ('dialog frame.border', 'fg:ansiblack bg:ansiwhite'),
            ('dialog frame.label', 'fg:ansiblack bg:ansiwhite'),
            ('dialog.textarea', 'fg:ansiwhite bg:ansiblack'),
        ])

        kb = KeyBindings()

        @kb.add('Q')
        @kb.add('q')
        def _(event):
            log.info("Q pressed. App exiting.")
            event.app.exit(exception=KeyboardInterrupt, style='class:aborting')

        @kb.add('H', filter=~modal_panel_visible | show_help)
        @kb.add('h', filter=~modal_panel_visible | show_help)
        @kb.add("enter", filter=show_help)
        def _(event):
            self.help_panel.visible = not self.help_panel.visible


        @kb.add('F', filter=~modal_panel_visible)
        @kb.add('f', filter=~modal_panel_visible)
        @kb.add("enter", filter=show_filters)
        def _(event):
            self.filter_panel.visible = not self.filter_panel.visible
            if self.filter_panel.visible:
                get_app().layout.focus(self.filter_panel.interface_textarea)
            else:
                self.filter = self.filter_panel.filter()
                self.transactions.assign([t for t in self.all_transactions if self.filter.passes(t) and self.passes_config_filters(t)])
                get_app().layout.focus(dummy_control)

        @kb.add("c-c")
        def _(event):
            active_frame = self.focusable[self.focus_index]
            active_frame.copy_to_clipboard()


        app = Application(
            layout,
            key_bindings=merge_key_bindings([
                kb,
                self.transaction_table.key_bindings(),
                self.structure_pane.key_bindings(),
                self.hexdump_pane.key_bindings()
            ]),
            full_screen=True,
            style=style
        )
        app.before_render += self.check_resize

        app.run()

    def check_resize(self, _):
        new_dimensions = os.get_terminal_size()
        if self.dimensions != new_dimensions:
            self.resize_components(new_dimensions)

    def resize_components(self, dimensions):
        self.dimensions = dimensions
        _, height = dimensions

        # Allow for the borders:
        # - top and bottom of transaction frame
        # - top and bottom of lower frames
        # - status bar
        border_allowance = 5
        available_height = height - border_allowance

        # Split into two halfs horizontally. If there are an odd number of lines give the extra to transactions.
        transactions_height = available_height - (available_height // 2)
        lower_panels_height = available_height // 2

        log.debug(f"New terminal dimension: {dimensions}")
        log.debug(f"{border_allowance=}, {transactions_height=}, {lower_panels_height=}, total={border_allowance+transactions_height+lower_panels_height}")

        self.transaction_table.resize(transactions_height)
        self.structure_pane.max_height = lower_panels_height
        self.hexdump_pane.max_lines = lower_panels_height

    def get_available_blocks(self):
        blocks: list[Block] = []
        # Retrieve every unhandled block currently available in the queue
        try:
            for _ in range(10):
                blocks.append(self.input_queue.get_nowait())
        except queue.Empty:
            pass
        return blocks
    
    def passes_config_filters(self, block):
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
        blocks = self.get_available_blocks()
        # For every block...
        for block in blocks:
            block = DisplayTransaction(block)

            if self.passes_config_filters(block) and ((not self.filter) or self.filter.passes(block)):
                self.transactions.append(block)

            self.all_transactions.append(block)

        return bool(blocks)