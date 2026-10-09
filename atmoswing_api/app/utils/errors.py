class InvalidInputError(ValueError):
    """
    A value provided by the client is invalid (e.g. a malformed date or an
    unknown entity). The message is returned to the client, so it must only
    describe the input and never contain server paths or internal details.
    """


class DataNotFoundError(FileNotFoundError):
    """
    The requested region or forecast does not exist. The message is returned
    to the client, so it must never contain server paths.
    """
