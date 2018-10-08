import aiohttp
import time
from typing import Union

from .errors import TwitchHTTPException


BASE = 'https://api.twitch.tv/helix/'
BASE5 = 'https://api.twitch.tv/kraken/'


class RateBucket:

    def __init__(self):
        self.tokens = 30
        self.refresh = time.time()

    def update_tokens(self):
        current = time.time()

        if self.tokens == 30:
            self.refresh = current + 60
        elif self.refresh <= current:
            self.tokens = 30
            self.refresh = current + 60

        self.tokens -= 1

        if self.tokens == 0:
            raise Exception(f'Rate limit exceeded please try again in {self.refresh - current}s')
        else:
            return self.tokens


rates = RateBucket()


def update_bucket(func):
    async def wrapper(*args, **kwargs):
        rates.update_tokens()

        return await func(*args, **kwargs)
    return wrapper


class HTTPSession:

    def __init__(self, loop, **attrs):
        self._id = attrs.get('client_id')
        self._session = aiohttp.ClientSession(loop=loop, headers={'Client-ID': self._id}, raise_for_status=True)

    async def _get(self, url: str):
        error_message = f'Error retrieving API data \'{url}\''

        try:
            body = await (await self._session.get(url)).json()

            if 'pagination' in body:
                cursor = body['pagination'].get('cursor')

                while cursor:
                    next_url = url + f'&after={cursor}'
                    next_body = await(await self._session.get(next_url)).json()
                    rates.update_tokens()
                    body['data'] += next_body['data']
                    cursor = next_body['pagination'].get('cursor')

        except aiohttp.ClientResponseError as e:
            # HTTP errors
            raise TwitchHTTPException(f'{error_message} - Status {e.code}')

        except aiohttp.ClientError:
            # aiohttp errors
            raise TwitchHTTPException(error_message)

        else:
            return body

    @staticmethod
    def _populate_channels(*channels: Union[str, int]):
        names = set()
        ids = set()

        for channel in channels:
            if isinstance(channel, str):
                if channel.isdigit():
                    # Handle ids in the string form
                    ids.add(int(channel))
                else:
                    names.add(channel)
            elif isinstance(channel, int):
                ids.add(channel)

        if len(names | ids) > 100:
            raise TwitchHTTPException('Bad Request - Total channels must not exceed 100.')

        return names, ids

    @update_bucket
    async def _get_users(self, *users: Union[str, int]):
        names, ids = self._populate_channels(*users)

        ids = [f'id={c}' for c in ids]
        names = [f'login={c}' for c in names]

        args = "&".join(ids + names)
        url = BASE + f'users?{args}'

        return await self._get(url)

    @update_bucket
    async def _get_chatters(self, channel: str):
        channel = channel.lower()
        url = f'http://tmi.twitch.tv/group/user/{channel}/chatters'
        return await self._get(url)

    async def _get_followers(self, channel: str):
        raise NotImplementedError

    @update_bucket
    async def _get_stream_by_id(self, channel: int):
        url = BASE + f'streams?user_id={channel}'
        return await self._get(url)

    @update_bucket
    async def _get_stream_by_name(self, channel: str):
        url = BASE + f'streams?user_login={channel}'
        return await self._get(url)

    @update_bucket
    async def _get_streams(self, *channels: Union[str, int]):
        names, ids = self._populate_channels(*channels)

        ids = [f'user_id={c}' for c in ids]
        names = [f'user_login={c}' for c in names]

        args = "&".join(ids + names)
        url = BASE + f'streams?{args}'

        return await self._get(url)

