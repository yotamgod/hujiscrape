import asyncio
import random

import aiohttp

from hujiscrape.fetch_tasks import FetchTask

DEFAULT_MAX_CONCURRENCY = 100
DEFAULT_TCP_SOCKET_LIMIT = 20


class Fetcher:
    def __init__(self, session: aiohttp.ClientSession = None, retries: int = 3, timeout: aiohttp.ClientTimeout = None,
                 max_concurrency: int | None = DEFAULT_MAX_CONCURRENCY,
                 tcp_socket_limit: int = DEFAULT_TCP_SOCKET_LIMIT, force_close_tcp: bool = False):
        """
        Parameters are tuned to work with Shnaton scraping.
        :param force_close_tcp: There is a bug in aiohttp that causes the following error if force_close isn't true:
                                error type: <class 'aiohttp.client_exceptions.ClientOSError'>, error msg: [Errno None]
                                Can not write request body for URL
        """
        self._retries = retries
        self._session: aiohttp.ClientSession = session or aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=tcp_socket_limit, force_close=force_close_tcp)
        )
        self._timeout = timeout or aiohttp.ClientTimeout(total=60, sock_connect=10, sock_read=10)
        self._semaphore = asyncio.BoundedSemaphore(max_concurrency) if max_concurrency else None

    async def __aenter__(self):
        await self._session.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._session.__aexit__(exc_type, exc_val, exc_tb)

    async def fetch(self, task: FetchTask) -> str:
        if not self._semaphore:
            response = await self._fetch_with_retries(task)
        else:
            async with self._semaphore:
                response = await self._fetch_with_retries(task)

        # No need to bound the io on local response.
        return await response.text()

    async def _fetch_with_retries(self, task: FetchTask) -> aiohttp.ClientResponse:
        for attempt in range(1, self._retries + 1):
            try:
                response = await self._session.request(
                    method=task.method,
                    url=task.url,
                    data=task.data,
                    params=task.query_params,
                    headers=task.headers,
                    verify_ssl=False,
                    allow_redirects=False,
                    timeout=self._timeout,
                )
                response.raise_for_status()
                return response
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                print(f"Request failed ({attempt}/{self._retries}): error type: {type(e)}, error msg: {e}")
                if attempt == self._retries:
                    raise e
                await asyncio.sleep(2 ** attempt + random.uniform(0, 1))  # Exponential backoff
