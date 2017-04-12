import asyncio

import aiohttp
from aiodns.error import DNSError


DEFAULT_HEADERS = {'User-agent': 'Mozilla/5.0 Gecko/20100101 glommer/1.0'}
DEFAULT_TIMEOUT = 6  # seconds


class DownloadError(Exception):     # TODO differentiate retryable and non-retryable errors

    def __init__(self, message, **kw):
        super(DownloadError, self).__init__(message)
        self.message = message
        self.code = kw.pop('code', None)

    def __repr__(self):
        args = ['%s=%r' % (k, v) for k, v in self.__dict__.items()]
        return "<%s(%s)>" % (self.__class__.__name__, ', '.join(args))


async def fetch(url, *, session):
    try:
        async with session.get(url, timeout=None) as resp:  # timeout=None to use session's timeout
            resp.raise_for_status()
            body = await resp.text(errors='ignore')

    except aiohttp.client_exceptions.ClientError as e:
        message = getattr(e, 'message', repr(e))
        code = getattr(e, 'code', None)
        raise DownloadError(message, code=code) from e

    except asyncio.TimeoutError as e:
        raise DownloadError(message='# Timeout') from e

    except DNSError as e:
        message = 'DNS error: %r' % e
        raise DownloadError(message) from e

    return resp, body


def make_session(loop, headers=None, *args, **kw):
    """Create and configure aiohttp.ClientSession"""

    sess_headers = DEFAULT_HEADERS
    if headers is not None:
        sess_headers.update(headers)

    timeout = kw.pop('timeout', DEFAULT_TIMEOUT)

    resolver = aiohttp.resolver.AsyncResolver(loop=loop)

    conn = aiohttp.TCPConnector(verify_ssl=False, limit_per_host=2, loop=loop, resolver=resolver)

    session = aiohttp.ClientSession(loop=loop, connector=conn, headers=sess_headers,
                                    read_timeout=timeout, conn_timeout=timeout)

    return session


async def download_to_future(url, fut, *, session):
    """Fetch and store result or exception in future"""
    try:
        resp, html = await fetch(url, session=session)
        fut.set_result((resp, html))

    except (DownloadError) as e:
        fut.set_exception(e)
