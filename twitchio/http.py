import aiohttp
import time
from typing import Union, Sequence

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
    """Rewrite Session (Will soon be the only Session)"""

    def __init__(self, loop, **attrs):
        self._id = attrs.get('client_id')
        self._session = aiohttp.ClientSession(loop=loop, headers={'Client-ID': self._id})

    @update_bucket
    async def _get_chatters(self, channel: str):
        channel = channel.lower()

        async with self._session.get(f'http://tmi.twitch.tv/group/user/{channel}/chatters') as resp:
            if resp.status == 200:
                data = await resp.json()
            else:
                raise TwitchHTTPException(f'Error retrieving chatters - Status {resp.status}')

            return data

    async def _get_followers(self, channel: str):
        raise NotImplementedError

    @update_bucket
    async def _get_stream_by_id(self, channel: int):
        url = BASE + f'streams?user_id={channel}'

        async with self._session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
            else:
                raise TwitchHTTPException(f'Error retrieving stream - Status {resp.status}')

            return data

    @update_bucket
    async def _get_stream_by_name(self, channel: str):
        url = BASE + f'streams?user_login={channel}'

        async with self._session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
            else:
                raise TwitchHTTPException(f'Error retrieving stream - Status {resp.status}')

            return data

    @update_bucket
    async def _get_streams_by_id(self, channels: Sequence[int]):
        ids = set()

        # Check if we are only getting ID's not names.
        for chan in channels:
            try:
                chan = int(chan)
            except (TypeError, ValueError):
                pass
            else:
                ids.add(chan)

        if len(ids) > 100:
            raise TwitchHTTPException('Bad Request - Total channels must not exceed 100.')

        ids = '&user_id='.join(str(c) for c in ids)
        url = BASE + f'streams?user_id={ids}'

        async with self._session.get(url) as resp:
            if resp.status == 200:
                cont = await resp.json()
            else:
                raise TwitchHTTPException(f'Bad Request while retrieving streams - {resp.status}')

        cursor = cont['pagination']
        if not cursor:
            if not cont['data']:
                return None

        data = {'data': []}
        for d in cont['data']:
            data['data'].append(d)

        while True:
            url = BASE + 'streams?after={}'.format(cursor)

            try:
                async with self._session.get(url) as resp:
                    cont = await resp.json()
            except Exception:
                break

            if resp.status > 200:
                break
            elif not cont['data']:
                break

            cursor = cont['pagination']

            for d in cont['data']:
                data['data'].append(d)

        return data


"""
def _check_cid(func):
    def deco(inst, *args, **kwargs):
        if not inst._cid:
            raise TwitchHTTPException('Client ID is required to access this endpoint.')
        return func(inst, *args, **kwargs)
    return deco
    
    
class HttpSession:
    # Legacy Session (deprecated)

    def __init__(self, session, **attrs):
        self._aiosess = session
        self._api_token = attrs.get('apitok', None)
        self._cid = attrs.get('cid', None)

        if self._api_token:
            self._theaders = {'Client-ID': self._cid}  # TODO
        else:
            self._theaders = {'Client-ID': self._cid}

    async def fetch(self, url: str, headers: dict = None, timeout: float = None,
                    return_type: str = None, **kwargs):

        async with self._aiosess.get(url, headers=headers, timeout=timeout, **kwargs) as resp:
            if return_type:
                cont = getattr(resp, return_type)
                return resp, await cont()
            else:
                return resp, None

    async def poster(self, url: str, headers: dict = None, timeout: float = None,
                     return_type: str = None, **kwargs):

        async with self._aiosess.post(url, headers=headers, timeout=timeout, **kwargs) as resp:
            if return_type:
                cont = getattr(resp, return_type)
                return resp, await cont()
            else:
                return resp, None

    # TODO Error Handling
    @_check_cid
    async def _get_streams(self, channels):

        cid = set()
        cname = set()

        for chan in channels:
            try:
                chan = int(chan)
            except (TypeError, ValueError):
                cname.add(chan)
            else:
                cid.add(chan)

        if len(cid) + len(cname) > 100:
            raise TwitchHTTPException('Bad Request:: Total channels must not exceed 100.')

        logins = '&user_login='.join(c for c in cname)
        cids = '&user_id='.join(c for c in cid)
        streams = logins + cids

        url = BASE + 'streams?user_login={}'.format(streams)

        try:
            resp, cont = await self.fetch(url, timeout=10, return_type='json', headers=self._theaders)
        except Exception as e:
            return TwitchHTTPException('There was a problem with your request. {}'.format(e))

        if not resp.status == 200:
            raise TwitchHTTPException('{}:: There was a problem with your request. Try again.'.format(resp.status))

        cursor = cont['pagination']
        if not cursor:
            if not cont['data']:
                return None
            return cont

        data = {'data': []}
        for d in cont['data']:
            data['data'].append(d)

        while True:
            url = BASE + 'streams?after={}'.format(cursor)

            try:
                resp, cont = await self.fetch(url, timeout=10, return_type='json', headers=self._theaders)
            except Exception:
                break

            if resp.status > 200:
                break
            elif not cont['data']:
                break
            else:
                cursor = cont['pagination']

            for d in cont['data']:
                data['data'].append(d)

        return data

    # TODO Error Handling
    @_check_cid
    async def _get_stream(self, channel):

        try:
            channel = int(channel)
        except (TypeError, ValueError):
            user_url = BASE + 'streams?user_login={}'.format(channel)
        else:
            user_url = BASE + 'streams?user_id={}'.format(channel)

        try:
            resp, cont = await self.fetch(user_url, timeout=10, return_type='json', headers=self._theaders)
        except Exception as e:
            return TwitchHTTPException('There was a problem with your request. {}'.format(e))

        if not resp.status == 200:
            raise TwitchHTTPException('{}:: There was a problem with your request. Try again.'.format(resp.status))

        return cont

    @_check_cid
    async def _get_followers(self, channel):
        # Todo Error Handling
        if not self._api_token:
            return

        channel = await self._get_stream(channel)

        url = BASE + 'follows?first=100?to_id={}'.format(channel['data'][0]['id'])

        try:
            resp, cont = await self.fetch(BASE.format(url), timeout=5, return_type='json', headers=self._theaders)
        except Exception as e:
            return TwitchHTTPException('There was a problem with your request. {}'.format(e))

        if len(resp['data']) > 99:
            pass
"""
