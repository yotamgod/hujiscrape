import http
from typing import Optional, Union, List, Dict

import aiohttp as aiohttp
from bs4 import BeautifulSoup

from magics import PRISA_MAXIMAL, TOAR_BOGER, TOAR_ANY, YEAR_ANY


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

    def _get_default_headers(self) -> dict:
        return {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/93.0.4577.63 Safari/537.36'}

    async def acollect(self) -> Optional[BeautifulSoup]:
        response = await self._session.request(self.method, self.url,
                                               data=self.data,
                                               params=self.params,
                                               headers=self.headers,
                                               verify_ssl=False)
        # if response.status != http.HTTPStatus.OK:
        #     return None
        # todo: handle errors
        return BeautifulSoup(await response.text(), 'html5lib')
        # return await self._parse_response(response)

    # async def _parse_response(self, response: aiohttp.ClientResponse) -> Union[List, Dict]:
    #     raise NotImplementedError()


class ShantonCourseFetcher(ShnatonFetcher):
    # SHNATON_URL = 'https://shnaton.huji.ac.il/index.php'
    SHNATON_URL = 'http://localhost:8080/Course.html'

    def __init__(self, year: int, course: str, headers: dict = None, session: aiohttp.ClientSession = None):
        data = {
            'peula': 'Simple',
            'maslul': 0,
            'shana': 0,
            'year': year,
            'course': course
        }

        # super().__init__('POST', self.SHNATON_URL, headers=headers, data=data, async_session=async_session)
        super().__init__('GET', self.SHNATON_URL, headers=headers, data=data, session=session)


class MaslulFetcher(ShnatonFetcher):
    """
    Returns a single page from a maslul search
    """

    # SHNATON_URL = 'https://shnaton.huji.ac.il/index.php'
    # SHNATON_URL = 'http://localhost:8080/maslul.html'
    SHNATON_URL = 'http://localhost:8080/OtherFolder/MaslulNoJs.html'

    def __init__(self, year: int, faculty: str, hug: str, maslul: str, toar: int = TOAR_ANY,
                 toar_year: int = YEAR_ANY, page: int = 1,
                 headers: dict = None, params: dict = None,
                 session: aiohttp.ClientSession = None):
        data = {
            'peula': 'Advanced',
            'year': year,
            'faculty': faculty,
            'hug': hug,
            'maslul': maslul,
            'prisa': PRISA_MAXIMAL,
            'toar': toar,
            'shana': toar_year,
            'starting': page
        }
        # super().__init__('POST', self.SHNATON_URL, headers, data, params, session=session)
        super().__init__('GET', self.SHNATON_URL, headers, data, params, session=session)
