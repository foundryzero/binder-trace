"""Help panel."""

from prompt_toolkit.layout import AnyContainer, HSplit
from prompt_toolkit.widgets import Box, Frame, Label


class HelpPanel:
    """HelpPanel definition."""

    def __init__(self) -> None:
        """Initialise HelpPanel."""
        self.visible = False

        float_frame = Box(
            padding_top=1,
            padding_left=2,
            padding_right=2,
            body=HSplit(
                children=[
                    Label(f"{'-' * 20}General{'-' * 27}"),
                    Label("up             Move up"),
                    Label("down           Move down"),
                    Label("shift + up     Page up"),
                    Label("shift + down   Page down"),
                    Label("home           Go to top"),
                    Label("end            Go to bottom"),
                    Label("tab            Next pane"),
                    Label("shift + tab    Previous pane"),
                    Label("ctrl + c       Copy pane to clipboard"),
                    Label("space          Pause/Unpause transaction recording"),
                    Label("c              Clear"),
                    Label("h              Help"),
                    Label("q              Quit"),
                    Label(f"{'-' * 20}Frequency Frame{'-' * 20}"),
                    Label("p              Toggle order asc/desc"),
                    Label("w              Jump to next interface"),
                    Label("s              Jump to previous interface"),
                    Label("a              Toggle all filters on"),
                    Label("n              Toggle all filters off"),
                    Label("enter          Toggle Filter"),
                ]
            ),
        )

        self.container = Frame(
            title="Help",
            body=float_frame,
            style="class:dialog.background",
            modal=True,
        )

    def __pt_container__(self) -> AnyContainer:
        """Get the internal container."""
        return self.container
