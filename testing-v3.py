import twitchio
import asyncio

import logging
logging.basicConfig()

async def main():
    tokens = twitchio.SimpleTokenHandler("3wgoa413eg0pe4208j9oc3tw7zatyb", "gp762nuuoqcoxypju8c569th9wz7q5", "1geo8xyn8f0k4iqhyadjya68jyer9ppfzm712az2l2cirz3vt5")

    async with twitchio.Client(tokens, initial_channels=["iamtomahawkx"]) as client:
        pager = client._http.get_users(ids=[], logins=["iamtomahawkx"])
        pager.set_adapter(lambda http, data: twitchio.User(http, data))
        print([x async for x in pager])

        await client.start()

asyncio.run(main())