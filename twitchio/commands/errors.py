from ..errors import TwitchIOBException


class TwitchIOCommandError(TwitchIOBException):
    def __init__(self, msg):
        super().__init__(msg)


class TwitchCommandNotFound(TwitchIOCommandError):
    def __init__(self, command):
        super().__init__('The command ({}) is invalid or was not found.'.format(command))


class TwitchInvalidPrefix(TwitchIOCommandError):
    def __init__(self, ptype: type):
        super().__init__('Invalid prefix type: {0}. Prefix must be of List, Tuple or String.'.format(ptype))


class TwitchTooManyArguments(TwitchIOCommandError):
    def __int__(self, msg):
        super().__init__(msg)


class TwitchMissingRequiredArguments(TwitchIOCommandError):
    def __int__(self, msg):
        super().__init__(msg)
