.. py:currentmodule:: twitchio

TwitchIO 2
============

Client
--------
.. autoclass:: Client
    :members: wait_for,
              get_channel,
              connected_channels,
              events,
              nick,
              create_user,
              fetch_users,
              fetch_clips,
              fetch_cheermotes,

Event Reference
-----------------
.. automethod:: Client.event_ready()
.. automethod:: Client.event_raw_data(data: str)
.. automethod:: Client.event_message(message: Message)
.. automethod:: Client.event_join(channel: Channel, user: User)
.. automethod:: Client.event_part(user: User)
.. automethod:: Client.event_mode(channel: Channel, user: User, status: str)
.. automethod:: Client.event_userstate(user: User)
.. automethod:: Client.event_raw_usernotice(channel: Channel, tags: dict)
.. automethod:: Client.event_usernotice_subscription(metadata)
.. automethod:: Client.event_error(error: Exception, data: str = None)