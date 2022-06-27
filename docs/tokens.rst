:orphan:

.. _tokens:

The new way to handle tokens
=============================

In previous versions of TwitchIO, we left token handling completely up to you, asking for a token when making the API call.
This led to some quite scattered code, as people made db calls throughout their code to fetch tokens for said API calls.
In TwitchIO 3, we've changed this. We've added in integrated token handling, with new classes to make managing tokens a breeze.
It even handles refreshing tokens by itself.

How does it work?
------------------

The library's new token handling system integrates into both HTTP and IRC, so there's no need to pass tokens to your
Client or Bot instance directly. When the library needs a token, it calls the corresponding method in your Token Handler,
which returns a :class:`~twitchio.Token`. The library then validates that token, satisfying twitch's wish for everyone
to validate tokens before using them, and grabbing info on the token, such as what scopes it has, and who the token is for.
By validating the token, the lib now knows whether it has a token that's allowed to make the request being asked.
After validating, the library caches the token, preventing it from asking the developer for a token every time it wants to
make a request. This can dramatically reduce DB calls or user prompts, as the developer's code doesn't have to run again
until the token becomes invalid, or the app calls for a scope that the token doesn't have.

Token objects
--------------

TwitchIO now bundles a Token object, which should be returned by any Token Handler method that returns a user OAuth token.
These objects take an access token and optionally a refresh token. Once these objects are in the Token Handler, it will
automatically handle validating the token, which twitch requires be done before using a token. It'll also handle refreshing
the token if it becomes invalid. To be notified when a token is refreshed, use the ``event_token_refreshed`` event.

But I don't need all these features!
-------------------------------------

Not to worry! For developers looking to run their entire bot off of one access token, we created a Simple Token Handler,
which returns the same token for anything and everything. We recommend only using this for testing, in production you should
use a fully features subclassed Token Handler. Using it is as simple as:

.. code-block:: python

    import twitchio
    handler = twitchio.SimpleTokenHandler("my_access_token", "my_client_id")
    client = twitchio.Client(handler)

The SimpleTokenHandler can also take a refresh token, client secret, and client token (for making api calls without using the user token).
For more information on the SimpleTokenHandler, see :class:`twitchio.SimpleTokenHandler`.


How do I use it?
-----------------

The first step to creating a token handler is subclassing :class:`twitchio.BaseTokenHandler`.
After doing that, you can override appropriate methods to customize them to your liking.
The methods that can be overriden are:

    - :meth:`~twitchio.BaseTokenHandler.get_user_token`
    - :meth:`~twitchio.BaseTokenHandler.get_client_token`
    - :meth:`~twitchio.BaseTokenHandler.get_client_credentials`
    - :meth:`~twitchio.BaseTokenHandler.get_irc_token`

Here is an example of a Token Handler that fetches from a database for API calls, and grabs a token from the bot's config for connecting to IRC:

.. warning::

    This example is not "plug-and-play". It assumes you have some skill in databasing, and can adapt it to your particular usecase.

.. code-block:: python

    import twitchio

    class MyCoolTokenHandler(twitchio.SimpleTokenHandler):
        async def get_user_token(self, user: twitchio.User | twitchio.PartialUser, scopes: list[str]) -> twitchio.Token:
            data = await self.client.db.fetch_row("SELECT token, refresh_token FROM tokens WHERE user_id = $1", user.id)
            return twitchio.Token(data['token'], data['refresh_token'])

        async def get_irc_token(self, shard_id: int) -> twitchio.Token:
            return twitchio.Token(self.client.config["irc_token"])

        async def get_client_credentials(self) -> tuple[str, str]:
            return self.client.config["client_id"], self.bot.config["client_secret"]
            # you don't *need* to return a client secret, however the library cannot refresh tokens without it!
