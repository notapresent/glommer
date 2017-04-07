import asyncio

import aiohttp
import async_timeout


DEFAULT_HEADERS = {'User-agent': 'Mozilla/5.0 Gecko/20100101 glommer/1.0'}
DEFAULT_TIMEOUT = 2  # seconds


class DownloadError(Exception):
    def __init__(self, *args, **kw):
        self.message = kw.get('message') or str(self)


async def fetch(url, sess, timeout=DEFAULT_TIMEOUT):
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


async def make_session(loop, headers=None):

    """Create and configure aiohttp.ClientSession"""

    if headers:
        sess_headers = DEFAULT_HEADERS
        sess_headers.update(headers)
    else:
        sess_headers = DEFAULT_HEADERS


    conn = aiohttp.TCPConnector(verify_ssl=False, limit_per_host=1, loop=loop)
    session = aiohttp.ClientSession(loop=loop, connector=conn, headers=sess_headers)
    return session

