import time

from queue import Queue

from prompt_toolkit.eventloop.inputhook import InputHookContext, set_eventloop_with_inputhook
from prompt_toolkit.application import get_app

from binder_trace.tui.interface import UserInterface

def start_ui(block_queue: Queue, pause_unpause, config):
    """
    Starts and runs the TUI, with the main event loop.

    Args:
        message_queue:
        block_queue:

    Returns:

    """
    # Create the UIDisplay with a given display filter
    ui = UserInterface(block_queue, pause_unpause, config)

    def inputhook(inputhook_context: InputHookContext):
        while not inputhook_context.input_is_ready():
            if ui.process_data():
                get_app().invalidate()
            else:
                time.sleep(0.1)

    set_eventloop_with_inputhook(inputhook=inputhook)

    ui.run()