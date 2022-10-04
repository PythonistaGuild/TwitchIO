.. currentmodule:: twitchio


Client Reference
================
Event, Client and Exceptions API reference.

.. note::

    For the **command extension** see: :any:`commands-ref`

Client
--------

.. attributetable:: Client

.. autoclass:: Client
    :members:
    :exclude-members: event_ready, event_raw_data, event_message,
                      event_join, event_part, event_mode, event_userstate,
                      event_raw_usernotice, event_usernotice_subscription, event_error,
                      event_channel_join_failure, event_reconnect

Event Reference
-----------------

.. automethod:: Client.event_ready()
.. automethod:: Client.event_reconnect()
.. automethod:: Client.event_raw_data(data: str)
.. automethod:: Client.event_message(message: Message)
.. automethod:: Client.event_join(channel: Channel, user: User)
.. automethod:: Client.event_part(user: User)
.. automethod:: Client.event_mode(channel: Channel, user: User, status: str)
.. automethod:: Client.event_userstate(user: User)
.. automethod:: Client.event_raw_usernotice(channel: Channel, tags: dict)
.. automethod:: Client.event_usernotice_subscription(metadata)
.. automethod:: Client.event_error(error: Exception, data: Optional[str] = None)
.. automethod:: Client.event_channel_join_failure(channel: str)

Exceptions
------------
.. autoexception:: TwitchIOException
.. autoexception:: AuthenticationError
.. autoexception:: InvalidContent
.. autoexception:: IRCCooldownError
.. autoexception:: EchoMessageWarning
.. autoexception:: NoClientID
.. autoexception:: NoToken
.. autoexception:: HTTPException
.. autoexception:: Unauthorized