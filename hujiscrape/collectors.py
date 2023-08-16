import time
from typing import Optional

import aiohttp as aiohttp
from bs4 import BeautifulSoup

from hujiscrape.magics import Prisa, Toar, ToarYear


class ShnatonFetcher:
    def __init__(self, method: str, url: str, headers: dict = None, data: dict = None, params: dict = None,
                 session: aiohttp.ClientSession = None):
        self.method = method
        self.url = url

        self.data = data or {}
        self.params = params or {}

        headers = headers or {}
        self.headers = {**self._get_default_headers(), **headers}

        self._session: Optional[
            aiohttp.ClientSession] = session or aiohttp.ClientSession()

        self._soup: Optional[BeautifulSoup] = None

    def _get_default_headers(self) -> dict:
        return {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/114.0.0.0 Safari/537.36'
        }

    async def acollect(self) -> Optional[BeautifulSoup]:
        before = time.time()
        response = await self._session.request(self.method, self.url,
                                               data=self.data,
                                               params=self.params,
                                               headers=self.headers,
                                               verify_ssl=False,
                                               allow_redirects=False)
        # todo: handle errors
        text = await response.text()
        self._soup = BeautifulSoup(text, 'html.parser')
        return self._soup

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


class MaslulFetcher(ShnatonFetcher):
    """
    Returns a single page from a maslul search
    """

    SHNATON_URL = 'https://shnaton.huji.ac.il/index.php'

    def __init__(self, year: int, faculty: str, hug: str, maslul: str, toar: Toar = Toar.Any,
                 toar_year: ToarYear = ToarYear.Any, page: int = 1,
                 session: aiohttp.ClientSession = None):
        data = {
            'peula': 'Advanced',
            'year': year,
            'faculty': faculty,
            'hug': hug,
            'maslul': maslul,
            'prisa': Prisa.Maximal.value,
            'toar': toar.value,
            'shana': toar_year.value,
            'starting': page
        }
        super().__init__('POST', self.SHNATON_URL, data=data, session=session)


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
