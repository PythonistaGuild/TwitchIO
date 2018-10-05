class TwitchIOBException(Exception):
    """Base exception class for TwitchIO."""


class AuthenticationError(TwitchIOBException):
    """Authentication error."""


class WSConnectionFailure(TwitchIOBException):
    """Exception raised when WS fails to connect."""


class ClientError(TwitchIOBException):
    pass


class InvalidContent(TwitchIOBException):
    pass


class TwitchHTTPException(TwitchIOBException):
    pass