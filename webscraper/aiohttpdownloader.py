import asyncio

import aiohttp
import async_timeout


class DownloadError(Exception):
    def __init__(self, *args, **kw):
        self.message = kw.get('message') or str(self)


async def fetch(url, sess, timeout=2):
    try:
        with async_timeout.timeout(timeout):
            resp = await sess.get(url)
            resp.raise_for_status()
            body = await resp.text(errors='ignore')

    except aiohttp.client_exceptions.ClientError as e:
        message = getattr(e, 'message', 'Generic download error')
        raise DownloadError(message=message) from e

    except asyncio.TimeoutError as e:
        raise DownloadError(message='Timeout') from e

    return resp, body


class Downloader:
    """Encapsulates http client session"""

    HEADERS = {'User-agent': 'Mozilla/5.0 Gecko/20100101 glommer/1.0'}
    TIMEOUT = 2  # seconds

    def __init__(self, loop=None):
        self._loop = loop or asyncio.get_event_loop()
        self._conn = aiohttp.TCPConnector(verify_ssl=False, limit_per_host=1)
        self._session = aiohttp.ClientSession(loop=self._loop, connector=self._conn, headers=self.HEADERS)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.teardown()

    async def get(self, url):
        return await fetch(url, self._session, self.TIMEOUT)

    async def teardown(self):
        await self._session.close()
