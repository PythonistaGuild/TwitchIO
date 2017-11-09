from .errors import TwitchHTTPException


class HttpSession:

    def __init__(self, session):
        self._aiosess = session
        self.headers = None

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

        resp, cont = await self.fetch('http://tmi.twitch.tv/group/user/{}/chatters'.format(name), timeout=5,
                                      return_type='json')

        if resp.status == 200:
            return cont
        else:
            raise TwitchHTTPException('Status: {} :: There was a problem retrieving chatters in channel: {}'
                                      .format(resp.status, name))
