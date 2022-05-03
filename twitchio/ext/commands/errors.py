class TwitchIOCommandError(Exception):
    pass


class CommandNotFoundError(TwitchIOCommandError):
    pass


class InvalidInvocationContext(TwitchIOCommandError):
    pass
