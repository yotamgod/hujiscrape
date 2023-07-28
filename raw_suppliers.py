import asyncio
import re
from functools import partial
from typing import Any, Union, List

import aiohttp
from bs4 import BeautifulSoup, Tag

from collectors import ShantonCourseFetcher, MaslulFetcher
from html_to_object import HtmlToCourse, Bs4Obj
from huji_objects import Course, Lesson
from magics import YEAR_ANY, TOAR_ANY, PASSING_TYPE_IDX


class RawSupplier:
    """
    Supplies Shnaton info as the HTML from a response.
    """

    async def supply(self) -> Any:
        """

        :return:
        """
        raise NotImplementedError()


class CourseSupplier(RawSupplier):
    """
    Supplies the html for a lecture in the Shnaton, between <a> tags.
    """

    async def supply(self) -> Course:
        raise NotImplementedError()


class StaticCourseSupplier(CourseSupplier):

    def __init__(self, course: Course) -> None:
        # assert html.name == 'div' and html.attrs.get('class') == 'courseTitle', "Invalid course element."
        self._course = course

    def supply(self) -> Course:
        return self._course


class RequestCourseSupplier(CourseSupplier):
    """
    Returns the direct html table containing a course's information.
    """

    def __init__(self, course_id: str, year: int):
        self._course_id_ = course_id
        self._course_fetcher = ShantonCourseFetcher(year, course_id)
        self._html_to_course = HtmlToCourse()

    async def supply(self) -> Course:
        soup = await self._course_fetcher.acollect()
        return self._html_to_course.convert(soup)


class MaslulSupplier(RawSupplier):

    async def supply(self) -> List[Course]:
        raise NotImplementedError()


class MaslulPageSupplier(MaslulSupplier):

    def __init__(self, year: int, faculty: str, hug: str, maslul: str, toar: int = TOAR_ANY,
                 toar_year: int = YEAR_ANY, page: int = 1, session: aiohttp.ClientSession = None) -> None:
        self._maslul_fetcher = MaslulFetcher(year, faculty, hug, maslul, toar, toar_year, page,
                                             session=session or aiohttp.ClientSession())
        self._html_to_course = HtmlToCourse()

    async def supply(self) -> List[Course]:
        soup = await self._maslul_fetcher.acollect()
        course_tds = [div.parent for div in soup.find_all('div', attrs={'class': 'courseTitle'})]
        return [self._html_to_course.convert(td) for td in course_tds]


class MaslulAllPageSupplier(MaslulSupplier):

    def __init__(self, year: int, faculty: str, hug: str, maslul: str, toar: int = TOAR_ANY,
                 toar_year: int = YEAR_ANY, session: aiohttp.ClientSession = None) -> None:
        self._session = session or aiohttp.ClientSession()
        self._year = year
        self._faculty = faculty
        self._hug = hug
        self._maslul = maslul
        self._toar = toar
        self._toar_year = toar_year

        # Using a fetcher to find the number of pages to download
        self._page_1_maslul_fetcher = MaslulFetcher(year, faculty, hug, maslul, toar, toar_year, 1,
                                                    session=self._session)

    async def supply(self) -> List[Course]:
        # Collect the first page to find out the number of pages required
        soup = await self._page_1_maslul_fetcher.acollect()
        page_info_text = soup.find('div', class_='facultyTitle').find_next('td').text
        page_number = int(re.findall(r'\d+', page_info_text)[1])
        semaphore = asyncio.Semaphore(3)
        page_supplier_coros = [self._collect_page(page, semaphore)
                               for page in range(page_number)]
        page_supplier_tasks = [asyncio.create_task(coro) for coro in page_supplier_coros]
        results = await asyncio.gather(*page_supplier_tasks)  # TODO: handle errors.

        # Flatten the list of lists of courses
        return [result for result_list in results for result in result_list]

    async def _collect_page(self, page: int, semaphore: asyncio.Semaphore):
        """
        Collects a page using a semaphore to avoid too many requests
        :param page: page to download
        :param semaphore: semaphore to use
        :return:
        """
        supplier = MaslulPageSupplier(self._year, self._faculty, self._hug, self._maslul,
                                      self._toar, self._toar_year, page, session=self._session)
        async with semaphore:
            return await supplier.supply()


class ExamSupplier(RawSupplier):
    """
    Supplies the exam info html for a course.
    """

    async def supply(self) -> Bs4Obj:
        raise NotImplementedError()
