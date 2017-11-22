from .errors import TwitchHTTPException

BASE = 'https://api.twitch.tv/helix/'
BASE5 = 'https://api.twitch.tv/kraken/'


def _check_cid(func):
    def deco(inst, *args, **kwargs):
        if not inst._cid:
            raise TwitchHTTPException('Client ID is required to access this endpoint.')
        return func(inst, *args, **kwargs)
    return deco


class HttpSession:

    def __init__(self, session, **attrs):
        self._aiosess = session
        self.headers = None

        self._api_token = attrs.get('apitok', None)
        self._cid = attrs.get('cid', None)

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

    async def _get_chatters(self, name):
        # Todo Error Handling

        name = name.lower()

        try:
            resp, cont = await self.fetch('http://tmi.twitch.tv/group/user/{}/chatters'.format(name), timeout=10,
                                          return_type='json')
        except Exception as e:
            raise TwitchHTTPException('Status: {} :: There was a problem retrieving chatters in channel: {}'
                                      .format(e, name))

        if resp.status == 200:
            return cont
        else:
            raise TwitchHTTPException('Status: {} :: There was a problem retrieving chatters in channel: {}'
                                      .format(resp.status, name))

    @_check_cid
    async def _get_stream(self, channel):
        # Todo Error Handling

        headers = {'Client-ID': self._cid}

        try:
            channel = int(channel)
        except (TypeError, ValueError):
            user_url = BASE + 'streams?user_login={}'.format(channel)
        else:
            user_url = BASE + 'streams?user_id={}'.format(channel)

        try:
            resp, cont = await self.fetch(user_url, timeout=5, return_type='json', headers=headers)
        except Exception as e:
            return TwitchHTTPException('There was a problem with your request. {}'.format(e))

        if not resp.status == 200:
            raise TwitchHTTPException('{}:: There was a problem with your request. Try again.'.format(resp.status))

        return cont

    async def _get_followers(self, channel):
        # Todo Error Handling

        if not self._api_token:
            return

        headers = {'Client-ID': self._cid}

        channel = await self._get_stream(channel)

        url = BASE + 'follows?first=100?to_id={}'.format(channel['data'][0]['id'])

        try:
            resp, cont = await self.fetch(BASE.format(url), timeout=5, return_type='json', headers=headers)
        except Exception as e:
            return TwitchHTTPException('There was a problem with your request. {}'.format(e))

        if len(resp['data']) > 99:
            pass
