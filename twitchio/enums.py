import enum


__all__ = ('WebhookMode',)


class WebhookMode(enum.Enum):
    subscribe = enum.auto()
    unsubscribe = enum.auto()
