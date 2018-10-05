from twitchio.errors import TwitchIOBException


class TwitchIOCommandError(TwitchIOBException):
    """Base Exception for errors raised by commands."""
    pass


class TwitchCommandNotFound(TwitchIOCommandError):
    """Exception raised when a command is not found."""
    pass


class TwitchMissingRequiredArguments(TwitchIOCommandError):
    """Exception raised when a required argument is not passed to a command."""


class TwitchBadArgument(TwitchIOCommandError):
    """Exception raised when a bad argument is passed to a command."""
