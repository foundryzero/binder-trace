"""ParseError."""


class ParseError(Exception):
    """
    Parsing Exception.

    An exception that wraps another exception, providing more details about the state of the current parcel that caused
    that exception.
    """

    def __init__(self, message: str):
        """Initialise ParseError."""
        super().__init__(message)
        self.message = message

    def __reduce__(self):
        """Reduce function."""
        return type(self), (self.message)
