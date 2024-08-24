from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .authentication import UserTokenPayload

async def event_oauth_authorized(payload: UserTokenPayload) -> None:
    """Event dispatched when a user authorizes your Client-ID via Twitch OAuth on a built-in web adapter.

    The default behaviour of this event is to add the authorized token to the client.
    See: [`Client.add_token`][twitchio.Client.add_token] for more details.

    Parameters
    ----------
    payload: UserTokenPayload
    """

async def event_ready() -> None:
    """Event dispatched when the Client is ready."""
