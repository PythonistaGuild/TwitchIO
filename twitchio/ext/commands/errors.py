class TwitchIOCommandError(Exception):
    pass


class CommandNotFoundError(TwitchIOCommandError):
    pass


class InvalidInvocationContext(TwitchIOCommandError):
    pass


class ComponentAlreadyExistsError(TwitchIOCommandError):
    pass


class ComponentLoadError(TwitchIOCommandError):
    pass


class ComponentNotFoundError(TwitchIOCommandError):
    pass


class ExtensionNotFoundError(TwitchIOCommandError):
    pass


class ExtensionAlreadyLoadedError(TwitchIOCommandError):
    pass


class ExtensionLoadFailureError(TwitchIOCommandError):
    pass


class ExtensionUnloadFailureError(TwitchIOCommandError):
    pass


class NoExtensionEntryPoint(TwitchIOCommandError):
    pass
