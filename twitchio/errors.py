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
