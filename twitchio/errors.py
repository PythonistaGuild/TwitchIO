class TwitchIOBException(Exception):
    """Base exception class for TwitchIO"""


class HostConnectionFailure(TwitchIOBException):
    def __init__(self, host, port):
        super().__init__('Incorrect address: host {} on port {}.'.format(host, port))


class ClientError(TwitchIOBException):
    def __init__(self, message):
        super().__init__(message)


class InvalidContent(TwitchIOBException):
    def __init__(self, message):
        super().__init__(message)


class HTTPException(TwitchIOBException):
    def __init__(self, message):
        super().__init__(message)

