import asyncio
import random
import time

import aiohttp
from tqdm import tqdm

from hujiscrape.fetch_tasks import FetchTask

DEFAULT_MAX_CONCURRENCY = 100
DEFAULT_TCP_SOCKET_LIMIT = 20


class Fetcher:
    def __init__(
        self,
        retries: int = 3,
        timeout: aiohttp.ClientTimeout = None,
        max_concurrency: int | None = DEFAULT_MAX_CONCURRENCY,
        tcp_socket_limit: int = DEFAULT_TCP_SOCKET_LIMIT,
        force_close_tcp: bool = False,
        debug: bool = False,
    ):
        """
        Parameters are tuned to work with Shnaton scraping.
        :param force_close_tcp: There is a bug in aiohttp that causes the following error if force_close isn't true:
                                error type: <class 'aiohttp.client_exceptions.ClientOSError'>, error msg: [Errno None]
                                Can not write request body for URL
        :param debug: Enable debug logging
        """
        self._debug = debug
        self._retries = retries

        # Soft timeout for aiohttp internals
        self._timeout = timeout or aiohttp.ClientTimeout(
            total=45, sock_connect=10, sock_read=10
        )
        # HARD timeout: This is the Zombie Killer. It must be > _timeout.
        self._hard_timeout = 60.0

        self._max_concurrency = max_concurrency or DEFAULT_MAX_CONCURRENCY
        self._semaphore = asyncio.BoundedSemaphore(self._max_concurrency)

        # Pass the socket limit correctly
        self._connector_kwargs = {
            "limit": tcp_socket_limit or DEFAULT_TCP_SOCKET_LIMIT,
            "force_close": force_close_tcp,
            "enable_cleanup_closed": True,
        }

        self._session = self._create_new_session()
        self._active_sessions = {self._session}

        self._refresh_lock = asyncio.Lock()
        self._network_status = asyncio.Event()
        self._network_status.set()

        self._active_sessions_count = 1
        self._request_count = 0
        self._recycle_threshold = 200
        self._last_error_time = 0

        self._slot_dashboard = {}

    def _log_debug(self, msg):
        if self._debug:
            tqdm.write(f"[{time.strftime('%H:%M:%S')}] {msg}")

    def _update_dash(self, task_id, status):
        self._slot_dashboard[task_id] = {"status": status, "time": time.time()}

    def _create_new_session(self):
        return aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(**self._connector_kwargs)
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if not self._session.closed:
            await self._session.close()
        for s in list(self._active_sessions):
            if not s.closed:
                await s.close()
        self._active_sessions.clear()

    async def _kill_session_delayed(self, session_to_kill, delay: float):
        try:
            await asyncio.sleep(delay)
            if not session_to_kill.closed:
                if self._debug and session_to_kill in self._active_sessions:
                    self._log_debug(
                        f"UNDERTAKER: Closing old session {id(session_to_kill)}..."
                    )
                await session_to_kill.close()
            if session_to_kill in self._active_sessions:
                self._active_sessions.discard(session_to_kill)
        except Exception:
            pass

    async def _background_restart_logic(self, faulty_session, delay):
        async with self._refresh_lock:
            if self._session is not faulty_session:
                return

            now = time.time()
            if delay > 0 and (now - self._last_error_time < 5):
                return
            self._last_error_time = now

            try:
                if delay > 0:
                    self._log_debug(
                        f"PAUSE: Network unstable. Cooling down for {delay}s..."
                    )
                    self._network_status.clear()
                    if not self._session.closed:
                        asyncio.create_task(
                            self._kill_session_delayed(self._session, 5.0)
                        )
                    await asyncio.sleep(delay)
                    self._log_debug("RESUME: Waking up...")
                else:
                    if not self._session.closed:
                        asyncio.create_task(
                            self._kill_session_delayed(self._session, 10.0)
                        )

                self._session = self._create_new_session()
                self._active_sessions.add(self._session)
                self._active_sessions_count += 1
                self._request_count = 0
            finally:
                self._network_status.set()

    def _trigger_restart(self, current_session, delay=0):
        asyncio.create_task(self._background_restart_logic(current_session, delay))

    # --- MAIN INTERFACE: Matches original (Returns str or Raises) ---
    async def fetch(self, task: FetchTask) -> str:
        task_id = id(asyncio.current_task())
        async with self._semaphore:
            self._update_dash(task_id, "Starting...")
            try:
                # We return the string directly, just like original ultimately did
                return await self._fetch_with_retries(task, task_id)
            finally:
                self._slot_dashboard.pop(task_id, None)

    async def _single_request_attempt(
        self, method, url, data, params, headers, session
    ):
        response = await session.request(
            method=method,
            url=url,
            data=data,
            params=params,
            headers=headers,
            verify_ssl=False,
            allow_redirects=False,
            timeout=self._timeout,
        )
        response.raise_for_status()
        text = await response.text()
        return text

    async def _fetch_with_retries(self, task: FetchTask, task_id: int) -> str:
        self._request_count += 1
        if self._request_count > self._recycle_threshold:
            self._trigger_restart(self._session, delay=0)
        course_id = task.data["course"]
        for attempt in range(1, self._retries + 1):
            await self._network_status.wait()

            self._update_dash(task_id, "Jitter Sleep")
            await asyncio.sleep(random.uniform(0.1, 1.0))

            current_session = self._session

            try:
                self._update_dash(task_id, f"Attempt {attempt}: Working...")

                # Hard Timeout wrapper: Essential for preventing hangs
                text = await asyncio.wait_for(
                    self._single_request_attempt(
                        task.method,
                        task.url,
                        task.data,
                        task.query_params,
                        task.headers,
                        current_session,
                    ),
                    timeout=self._hard_timeout,
                )
                return text

            except (
                aiohttp.ClientError,
                asyncio.TimeoutError,
                OSError,
                asyncio.CancelledError,
                RuntimeError,
            ) as e:
                is_cancelled = isinstance(e, asyncio.CancelledError)
                is_session_closed = isinstance(
                    e, RuntimeError
                ) and "Session is closed" in str(e)

                if (is_cancelled or is_session_closed) and self._debug:
                    self._log_debug(
                        f"RACE: Task {task_id} caught in session rotation - {course_id}"
                    )

                if attempt == 1 and not (is_cancelled or is_session_closed):
                    if self._debug:
                        self._log_debug(f"TRIGGER: {type(e).__name__} on {course_id}")
                    self._trigger_restart(current_session, delay=30)

                if attempt == self._retries:
                    self._log_debug(
                        f"FAILED: {course_id} after {self._retries} attempts. Raising error."
                    )
                    raise e

                self._update_dash(task_id, f"Error {type(e).__name__}: Sleep")

                # Exponential backoff (original behavior) + Jitter
                backoff = 2**attempt + random.uniform(0, 1)
                await asyncio.sleep(backoff)

        raise Exception(
            f"Failed to fetch {course_id} for unknown reasons"
        )  # Should not reach here
