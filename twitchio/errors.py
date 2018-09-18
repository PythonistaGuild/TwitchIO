class TwitchIOBException(Exception):
    """Base exception class for TwitchIO"""


class WSConnectionFailure(TwitchIOBException):
    """Exception raised when WS fails to connect."""


class ClientError(TwitchIOBException):
    def __init__(self, message, **kwargs):
        super().__init__(message)


class InvalidContent(TwitchIOBException):
    def __init__(self, message):
        super().__init__(message)


class TwitchHTTPException(TwitchIOBException):
    def __init__(self, message):
        super().__init__(message)