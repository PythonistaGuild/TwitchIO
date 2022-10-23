class TwitchIOCommandError(Exception):

    def __init__(self, *args, **kwargs):
        super().__init__(*args)

        self.original: Exception | None = kwargs.get('original', None)


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
