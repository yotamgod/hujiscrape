import asyncio
import random
from typing import Optional

import aiohttp as aiohttp
from bs4 import BeautifulSoup


class ShnatonFetcher:
    """
    A class that handles the requesting process to the Shanaton website.
    This does not include the session handling, because different scraping processes might require different sessions.
    """

    def __init__(self, method: str, url: str, headers: dict = None, data: dict = None, params: dict = None,
                 session: aiohttp.ClientSession = None, retries: int = 3):
        self.method = method
        self.url = url

        self.data = data or {}
        self.params = params or {}

        headers = headers or {}
        self.headers = {**self._get_default_headers(), **headers}

        self._retries = retries

        self._session: aiohttp.ClientSession = session or aiohttp.ClientSession()

        self._soup: Optional[BeautifulSoup] = None

    def _get_default_headers(self) -> dict:
        return {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/114.0.0.0 Safari/537.36'
        }

    async def afetch(self) -> Optional[BeautifulSoup]:

        # todo: handle errors
        response = await self._afetch_with_retries()
        text = await response.text()
        self._soup = BeautifulSoup(text, 'html.parser')
        return self._soup

    async def _afetch_with_retries(self) -> aiohttp.ClientResponse:
        for attempt in range(1, self._retries + 1):
            try:
                return await self._session.request(
                    self.method, self.url,
                    data=self.data,
                    params=self.params,
                    headers=self.headers,
                    verify_ssl=False,
                    allow_redirects=False
                )
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                print(f"Request failed ({attempt}/{self._retries}): {e}")
                if attempt == self._retries:
                    raise e
                await asyncio.sleep(2 ** attempt + random.uniform(0, 1))  # Exponential backoff

    @property
    def soup(self) -> Optional[BeautifulSoup]:
        """
        :return: the last soup collected by the fetcher, None if it wasn't collected yet
        """
        return self._soup


class ShantonCourseFetcher(ShnatonFetcher):
    SHNATON_URL = 'https://shnaton.huji.ac.il/index.php'

    def __init__(self, course_id: str, year: int, session: aiohttp.ClientSession = None):
        data = {
            'peula': 'Simple',
            'maslul': 0,
            'shana': 0,
            'year': year,
            'course': course_id
        }

        super().__init__('POST', self.SHNATON_URL, data=data, session=session)

    async def afetch(self) -> Optional[BeautifulSoup]:
        """
        Returns the soup of the course page, or None if the course wasn't found.
        """
        soup = await super().afetch()

        # If a course wasn't found, it will be specified in the data-course-title div.
        course_not_found_text = "לא נמצא קורס"
        if course_not_found_text in soup.find('div', class_='data-course-title').text.strip():
            return None

        return soup


class ExamFetcher(ShnatonFetcher):
    SHNATON_URL = 'https://shnaton.huji.ac.il/index.php'

    def __init__(self, course_id: str, year: int, session: aiohttp.ClientSession = None):
        data = {
            'peula': 'CourseD',
            'year': year,
            'detail': 'examDates',
            'course': course_id
        }
        super().__init__('POST', self.SHNATON_URL, data=data, session=session)
