.. currentmodule:: twitchio.ext.eventsub

.. _eventsub_ref:

EventSub Ext
=============

The EventSub ext is made to receive eventsub webhook notifications from twitch.
For those not familiar with eventsub, it allows you to subscribe to certain events, and when these events happen,
Twitch will send you an HTTP request containing information on the event. This ext abstracts away the complex portions of this,
integrating seamlessly into the twitchio Client event dispatching system.

.. warning::
    This ext requires you to have a public facing ip AND domain, and to be able to receive inbound requests.

.. note::
    Twitch requires EventSub targets to have TLS/SSL enabled (https). TwitchIO does not support this, as such you should
    use a reverse proxy such as ``nginx`` to handle TLS/SSL.


A Quick Example
----------------

.. code-block:: python3

    import twitchio
    from twitchio.ext import eventsub, commands
    bot = commands.Bot(token="...")
    eventsub_client = eventsub.EventSubClient(bot, "some_secret_string", "https://your-url.here/callback")
    # when subscribing (you can only await inside coroutines)

    await eventsub_client.subscribe_channel_subscriptions(channel_ID)

    @bot.event()
    async def eventsub_notification_subscription(payload: eventsub.ChannelSubscribeData):
      ...

    bot.loop.create_task(eventsub_client.listen(port=4000))
    bot.loop.create_task(bot.start())
    bot.loop.run_forever()


Running Eventsub Inside a Commands Bot
---------------------------------------

.. code-block:: python3

    import twitchio
    from twitchio.ext import commands, eventsub

    esbot = commands.Bot.from_client_credentials(client_id='...',
                                             client_secret='...')
    esclient = eventsub.EventSubClient(esbot,
                                       webhook_secret='...',
                                       callback_route='https://your-url.here/callback')


    class Bot(commands.Bot):

        def __init__(self):
            super().__init__(token='...', prefix='!', initial_channels=['channel'])

        async def __ainit__(self) -> None:
            self.loop.create_task(esclient.listen(port=4000))

            try:
                await esclient.subscribe_channel_follows_v2(broadcaster=some_channel_ID, moderator=a_channel_mod_ID)
            except twitchio.HTTPException:
                pass

        async def event_ready(self):
            print('Bot is ready!')


    bot = Bot()
    bot.loop.run_until_complete(bot.__ainit__())


    @esbot.event()
    async def event_eventsub_notification_followV2(payload: eventsub.ChannelFollowData) -> None:
        print('Received event!')
        channel = bot.get_channel('channel')
        await channel.send(f'{payload.data.user.name} followed woohoo!')

    bot.run()


Event Reference
----------------
This is a list of events dispatched by the eventsub ext.

.. function:: event_eventsub_notification_user_authorization_grant(event: UserAuthorizationGrantedData)

    Called when your app has had access granted on a channel.

.. function:: event_eventsub_revokation(event: RevokationEvent)

    Called when your app has had access revoked on a channel.

.. function:: event_eventsub_webhook_callback_verification(event: ChallengeEvent)

    Called when Twitch sends a challenge to your server.

    .. note::
        You generally won't need to interact with this event. The ext will handle responding to the challenge automatically.

.. function:: event_eventsub_notification_follow(event: ChannelFollowData)

    Called when someone creates a follow on a channel you've subscribed to.

.. function:: event_eventsub_notification_subscription(event: ChannelSubscribeData)

    Called when someone subscribes to a channel that you've subscribed to.

.. function:: event_eventsub_notification_subscription_end(event: ChannelSubscriptionEndData)

    Called when a subscription to a channel that you've subscribed to ends.

.. function:: event_eventsub_notification_subscription_gift(event: ChannelSubscriptionGiftData)

    Called when someone gifts a subscription to a channel that you've subscribed to.

.. function:: event_eventsub_notification_subscription_message(event: ChannelSubscriptionMessageData)

    Called when someone resubscribes with a message to a channel that you've subscribed to.

.. function:: event_eventsub_notification_cheer(event: ChannelCheerData)

    Called when someone cheers on a channel you've subscribed to.

.. function:: event_eventsub_notification_raid(event: Channel)

    Called when someone raids a channel you've subscribed to.

.. function:: event_eventsub_notification_poll_begin(event: PollBeginProgressData)

    Called when a poll begins on a channel you've subscribed to.

.. function:: event_eventsub_notification_poll_progress(event: PollBeginProgressData)

    Called repeatedly while a poll is running on a channel you've subscribed to.

.. function:: event_eventsub_notification_poll_end(event: PollEndData)

    Called when a poll ends on a channel you've subscribed to.

.. function:: event_eventsub_notification_prediction_begin(event: PredictionBeginProgressData)

    Called when a prediction starts on a channel you've subscribed to.

.. function:: event_eventsub_notification_prediction_progress(event: PredictionBeginProgressData)

    Called repeatedly while a prediction is running on a channel you've subscribed to.

.. function:: event_eventsub_notification_prediction_lock(event: PredictionLockData)

    Called when a prediction locks on a channel you've subscribed to.

.. function:: event_eventsub_notification_prediction_end(event: PredictionEndData)

    Called when a prediction ends on a channel you've subscribed to.

.. function:: event_eventsub_notification_stream_start(event: StreamOnlineData)

    Called when a stream starts on a channel you've subscribed to.

.. function:: event_eventsub_notification_stream_end(event: StreamOfflineData)

    Called when a stream ends on a channel you've subscribed to.

.. function:: event_eventsub_notification_channel_goal_begin(event: ChannelGoalBeginProgressData)

    Called when a streamer starts a goal on their channel.

.. function:: event_eventsub_notification_channel_goal_progress(event: ChannelGoalBeginProgressData)

    Called when there is an update event to a channel's goal.

.. function:: event_eventsub_notification_channel_goal_end(event: ChannelGoalEndData)

    Called when someone ends a goal on their channel.

.. function:: event_eventsub_notification_hypetrain_begin(event: HypeTrainBeginProgressData)

    Called when a hype train starts on their channel.

.. function:: event_eventsub_notification_hypetrain_progress(event: HypeTrainBeginProgressData)

    Called when a hype train receives an update on their channel.

.. function:: event_eventsub_notification_hypetrain_end(event: HypeTrainEndData)

    Called when a hype train ends on their channel.

.. function:: event_eventsub_notification_channel_shield_mode_begin(event: ChannelShieldModeBeginData)

    Called when a channel's Shield Mode status is activated.

.. function:: event_eventsub_notification_channel_shield_mode_end(event: ChannelShieldModeEndData)

    Called when a channel's Shield Mode status is deactivated.

.. function:: event_eventsub_notification_channel_shoutout_create(event: ChannelShoutoutCreateData)

    Called when a channel sends a shoutout.

.. function:: event_eventsub_notification_channel_shoutout_receive(event: ChannelShoutoutReceiveData)

    Called when a channel receives a shoutout.

API Reference
--------------

.. attributetable:: EventSubClient

.. autoclass:: EventSubClient
    :members:
    :undoc-members:

.. attributetable:: Subscription

.. autoclass:: Subscription
    :members:
    :inherited-members:

.. attributetable:: Headers

.. autoclass:: Headers
    :members:
    :inherited-members:

.. attributetable::: ChannelBanData

.. autoclass:: ChannelBanData
    :members:
    :inherited-members:

.. attributetable::: ChannelShieldModeBeginData

.. autoclass:: ChannelShieldModeBeginData
    :members:
    :inherited-members:

.. attributetable::: ChannelShieldModeEndData

.. autoclass:: ChannelShieldModeEndData
    :members:
    :inherited-members:

.. attributetable::: ChannelShoutoutCreateData

.. autoclass:: ChannelShoutoutCreateData
    :members:
    :inherited-members:

.. attributetable::: ChannelShoutoutReceiveData

.. autoclass:: ChannelShoutoutReceiveData
    :members:
    :inherited-members:

.. attributetable::: ChannelSubscribeData

.. autoclass:: ChannelSubscribeData
    :members:
    :inherited-members:

.. attributetable::: ChannelSubscriptionGiftData

.. autoclass:: ChannelSubscriptionGiftData
    :members:
    :inherited-members:

.. attributetable::: ChannelSubscriptionMessageData

.. autoclass:: ChannelSubscriptionMessageData
    :members:
    :inherited-members:

.. attributetable::: ChannelCheerData

.. autoclass:: ChannelCheerData
    :members:
    :inherited-members:

.. attributetable::: ChannelUpdateData

.. autoclass:: ChannelUpdateData
    :members:
    :inherited-members:

.. attributetable::: ChannelFollowData

.. autoclass:: ChannelFollowData
    :members:
    :inherited-members:

.. attributetable::: ChannelRaidData

.. autoclass:: ChannelRaidData
    :members:
    :inherited-members:

.. attributetable::: ChannelModeratorAddRemoveData

.. autoclass:: ChannelModeratorAddRemoveData
    :members:
    :inherited-members:

.. attributetable::: ChannelGoalBeginProgressData

.. autoclass:: ChannelGoalBeginProgressData
    :members:
    :inherited-members:

.. attributetable::: ChannelGoalEndData

.. autoclass:: ChannelGoalEndData
    :members:
    :inherited-members:

.. attributetable::: CustomReward

.. autoclass:: CustomReward
    :members:
    :inherited-members:

.. attributetable::: CustomRewardAddUpdateRemoveData

.. autoclass:: CustomRewardAddUpdateRemoveData
    :members:
    :inherited-members:

.. attributetable::: CustomRewardRedemptionAddUpdateData

.. autoclass:: CustomRewardRedemptionAddUpdateData
    :members:
    :inherited-members:

.. attributetable::: HypeTrainContributor

.. autoclass:: HypeTrainContributor
    :members:
    :inherited-members:

.. attributetable::: HypeTrainBeginProgressData

.. autoclass:: HypeTrainBeginProgressData
    :members:
    :inherited-members:

.. attributetable::: HypeTrainEndData

.. autoclass:: HypeTrainEndData
    :members:
    :inherited-members:

.. attributetable::: PollChoice

.. autoclass:: PollChoice
    :members:
    :inherited-members:

.. attributetable::: BitsVoting

.. autoclass:: BitsVoting
    :members:
    :inherited-members:

.. attributetable::: ChannelPointsVoting

.. autoclass:: ChannelPointsVoting
    :members:
    :inherited-members:

.. attributetable::: PollStatus

.. autoclass:: PollStatus
    :members:
    :inherited-members:

.. attributetable::: PollBeginProgressData

.. autoclass:: PollBeginProgressData
    :members:
    :inherited-members:

.. attributetable::: PollEndData

.. autoclass:: PollEndData
    :members:
    :inherited-members:

.. attributetable::: Predictor

.. autoclass:: Predictor
    :members:
    :inherited-members:

.. attributetable::: PredictionOutcome

.. autoclass:: PredictionOutcome
    :members:
    :inherited-members:

.. attributetable::: PredictionStatus

.. autoclass:: PredictionStatus
    :members:
    :inherited-members:

.. attributetable::: PredictionBeginProgressData

.. autoclass:: PredictionBeginProgressData
    :members:
    :inherited-members:

.. attributetable::: PredictionLockData

.. autoclass:: PredictionLockData
    :members:
    :inherited-members:

.. attributetable::: PredictionEndData

.. autoclass:: PredictionEndData
    :members:
    :inherited-members:

.. attributetable::: StreamOnlineData

.. autoclass:: StreamOnlineData
    :members:
    :inherited-members:

.. attributetable::: StreamOfflineData

.. autoclass:: StreamOfflineData
    :members:
    :inherited-members:

.. attributetable::: UserAuthorizationRevokedData

.. autoclass:: UserAuthorizationRevokedData
    :members:
    :inherited-members:

.. attributetable::: UserUpdateData

.. autoclass:: UserUpdateData
    :members:
    :inherited-members:

