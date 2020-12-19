class TwitchIOException(Exception):
    pass


class AuthenticationError(TwitchIOException):
    pass


class InvalidContent(TwitchIOException):
    pass


class IRCCooldownError(TwitchIOException):
    pass


class EchoMessageWarning(TwitchIOException):
    pass

class NoClientID(TwitchIOException):
    pass

class NoToken(TwitchIOException):
    pass

class HTTPException(TwitchIOException):
    pass

class Unauthorized(HTTPException):
    pass