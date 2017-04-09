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


async def fetch(url, sess):
    try:
        async with await sess.get(url, timeout=None) as resp:   # timeout=None to use session's timeout
            resp.raise_for_status()
            body = await resp.text(errors='ignore')

    except aiohttp.client_exceptions.ClientError as e:
        message = getattr(e, 'message', repr(e))
        code = getattr(e, 'code')
        raise DownloadError(message, code=code) from e

    except asyncio.TimeoutError as e:
        raise DownloadError(message='# Timeout') from e

    except DNSError as e:
        message = 'DNS error: %r' % e
        raise DownloadError(message) from e

    return resp, body


async def make_session(loop, headers=None, *args, **kw):

    """Create and configure aiohttp.ClientSession"""

    if headers:
        sess_headers = DEFAULT_HEADERS
        sess_headers.update(headers)
    else:
        sess_headers = DEFAULT_HEADERS

    timeout = kw.pop('timeout', DEFAULT_TIMEOUT)

    resolver = aiohttp.resolver.AsyncResolver(loop=loop)
    conn = aiohttp.TCPConnector(verify_ssl=False, limit_per_host=2, loop=loop, resolver=resolver)
    session = aiohttp.ClientSession(loop=loop, connector=conn, headers=sess_headers,
                                    read_timeout=timeout, conn_timeout=timeout)

    return session
