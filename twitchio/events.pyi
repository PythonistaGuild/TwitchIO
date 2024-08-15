from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .authentication import UserTokenPayload

async def event_oauth_authorized(payload: UserTokenPayload) -> None:
    """Event dispatched when a user authorizes via Twitch OAuth on a built-in web adapter.

    Parameters
    ----------
    payload: UserTokenPayload
    """

async def event_ready() -> None:
    """Event dispatched when the Client is ready."""
