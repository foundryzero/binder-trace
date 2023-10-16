class ParseError(Exception):
    """
    An exception that wraps another exception, providing more details about the state of the current parcel that caused
    that exception.
    """

    def __init__(self, message, parcelSoFar=None, extras=None, wrapped=None):
        super().__init__(message)
        self.message = message
        self.parcel = parcelSoFar
        self.extras = extras
        self.wrapped = wrapped

    def __reduce__(self):
        return type(self), (self.message, self.parcel, self.extras, self.wrapped)
