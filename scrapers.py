import asyncio
import re
from typing import Any, List, AsyncIterator, Tuple, Set, Generator

import aiohttp
from bs4 import BeautifulSoup

from collectors import ShantonCourseFetcher, MaslulFetcher, ExamFetcher
from html_to_object import HtmlToCourse, HtmlToExams, HtmlPageToCourses
from huji_objects import Course, Exam
from magics import Toar, ToarYear


class HujiObjectSupplier:
    """
    Supplies Shnaton info as the HTML from a response.
    """

    async def supply(self) -> Any:
        raise NotImplementedError()

    async def __aenter__(self) -> 'HujiObjectSupplier':
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class SessionSupplierMixin:

    def __init__(self, *args, session: aiohttp.ClientSession = None, **kwargs) -> None:
        self._session = session or aiohttp.ClientSession()
        super().__init__(*args, **kwargs)

    async def __aenter__(self):
        await self._session.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._session.__aexit__(exc_type, exc_val, exc_tb)


class ShnatonSupplierMixin(SessionSupplierMixin):
    """
    A supplier for data from the shnaton.
    Includes a session with a limit on the number of concurrent requests.
    """
    DEFAULT_CONCURRENT_REQUESTS = 100

    def __init__(self, *args, session: aiohttp.ClientSession = None,
                 concurrent_requests: int = DEFAULT_CONCURRENT_REQUESTS,
                 **kwargs):
        """
        :param session: Session to use. If not specified a new one will be created.
        :param concurrent_requests: If a new session is created, limit on number of concurrent requests.
        """
        session = session or aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=concurrent_requests)
        )
        kwargs['session'] = session
        super().__init__(*args, **kwargs)


class AbstractShnatonCourseSupplier(ShnatonSupplierMixin, HujiObjectSupplier):
    """
    Abstract class that supplies a list of courses from the shnaton.
    Includes an option to add exams to output courses.
    """

    def __init__(self, year: int, include_exams=True, **kwargs) -> None:

        super().__init__(**kwargs)
        self._year = year
        self._include_exams = include_exams

    async def supply(self) -> List[Course]:
        courses = []

        # Add exams to courses if needed
        exam_tasks = []

        async for course in self._supply():
            courses.append(course)

            if self._include_exams:
                exam_tasks.append(
                    asyncio.create_task(self._add_exams([course]))
                )
        await asyncio.gather(*exam_tasks)
        return courses

    async def _supply(self) -> AsyncIterator[Course]:
        raise NotImplementedError()

    async def _add_exams(self, courses: List[Course]):
        """
        A generic method to supply exams.
        If using to collect exams for multiple courses, it is better to supply a session and a semaphore.
        :return:
        """

        exam_coros = [self._get_exams(course) for course in courses]
        results: List[List[Exam]] = await asyncio.gather(*exam_coros)
        for idx, result in enumerate(results):
            courses[idx].exams = result

    async def _get_exams(self, course: Course):
        """
        Returns the exams for a specific course.
        :param course:
        :return:
        """
        exam_supplier = ExamSupplier(course.course_id, self._year, session=self._session)
        return await exam_supplier.supply()


class ShnatonCourseSupplier(AbstractShnatonCourseSupplier):
    """
    Supplies courses from shnaton by id.
    """

    def __init__(self, course_ids: List[str], year: int, include_exams=True, **kwargs) -> None:
        super().__init__(year=year, include_exams=include_exams, **kwargs)
        self._course_ids = course_ids
        self._html_to_course = HtmlToCourse()

    async def _supply(self) -> AsyncIterator[Course]:
        coros = [self._collect_course(course_id) for course_id in self._course_ids]
        for task in asyncio.as_completed(coros):
            course = await task
            yield course

    async def _collect_course(self, course_id: str) -> Course:
        fetcher = ShantonCourseFetcher(course_id, self._year, self._session)
        soup = await fetcher.acollect()
        course = self._html_to_course.convert(soup)
        return course


class MaslulPageSupplier(AbstractShnatonCourseSupplier):

    def __init__(self, year: int, faculty: str, hug: str, maslul: str, toar: Toar = Toar.Any,
                 toar_year: ToarYear = ToarYear.Any, page: int = 1, include_exams=True,
                 **kwargs) -> None:
        super().__init__(year=year, include_exams=include_exams, **kwargs)
        self._faculty = faculty
        self._hug = hug
        self._maslul = maslul
        self._toar = toar
        self._toar_year = toar_year
        self._page = page
        self._html_to_courses = HtmlPageToCourses()

    async def _supply(self) -> AsyncIterator[Course]:
        fetcher = MaslulFetcher(self._year, self._faculty, self._hug, self._maslul, self._toar, self._toar_year,
                                self._page, self._session)
        soup = await fetcher.acollect()
        for course in self._html_to_courses.convert(soup):
            yield course


class MaslulAllPageSupplier(AbstractShnatonCourseSupplier):

    def __init__(self, year: int, faculty: str, hug: str, maslul: str, toar: Toar = Toar.Any,
                 toar_year: ToarYear = ToarYear.Any, include_exams=True,
                 **kwargs) -> None:
        super().__init__(year=year, include_exams=include_exams, **kwargs)
        self._faculty = faculty
        self._hug = hug
        self._maslul = maslul
        self._toar = toar
        self._toar_year = toar_year

    async def _get_page_bounds(self, soup: BeautifulSoup) -> Tuple[int, int]:

        page_info_text = soup.find('div', class_='facultyTitle').find_next('td').text.strip()

        if not page_info_text:  # Happens if there is only a single page
            return 1, 1
        from_page, to_page = [int(number) for number in re.findall(r'\d+', page_info_text)]
        return from_page, to_page

    async def _supply(self) -> AsyncIterator[Course]:
        # Collect the first page to find out the number of pages required
        first_page_fetcher = MaslulFetcher(self._year, self._faculty, self._hug, self._maslul, self._toar,
                                           self._toar_year, 1, self._session)
        first_page_soup = await first_page_fetcher.acollect()
        page_from, page_to = await self._get_page_bounds(first_page_soup)

        # Go over pages from the second page until the last one and collect them.
        page_supplier_coros = [self._collect_page(page) for page in range(page_from + 1, page_to + 1)]

        yielded_course_ids = set()
        for task in asyncio.as_completed(page_supplier_coros):
            course_list = await task
            for course in self._yield_new_courses(course_list, yielded_course_ids):
                yield course

        # Remember to yield the remaining courses from the first page
        for course in self._yield_new_courses(HtmlPageToCourses().convert(first_page_soup), yielded_course_ids):
            yield course
        # # Yield only unique courses
        # new_courses = [course for course in course_list if course.course_id not in course_ids]
        # for course in new_courses:
        #     course_ids.add(course.course_id)
        #     yield course

    def _yield_new_courses(self, course_list: List[Course],
                           yielded_course_ids: Set[str]) -> Generator[Course, None, None]:
        """
        A helper function that yields courses that have not been yielded yet, and updates the yielded course set.
        :param course_list: list of courses to be filtered and yielded
        :param yielded_course_ids: set of course ids that have already been yielded
        :return:
        """
        new_courses = [course for course in course_list if course.course_id not in yielded_course_ids]
        for course in new_courses:
            yield course
            yielded_course_ids.add(course.course_id)

    async def _collect_page(self, page: int) -> List[Course]:
        """
        Collects a page using the MaslulPageSupplier
        :param page: page to download
        :return: a list of courses
        """
        # Only include exams as a part of the current supplier (so they are not added twice).
        supplier = MaslulPageSupplier(self._year, self._faculty, self._hug, self._maslul,
                                      self._toar, self._toar_year, page, include_exams=False, session=self._session)

        print(f"Requesting page: {page}")
        course_list = await supplier.supply()
        print(f"Page got: {page}")
        return course_list


class ExamSupplier(ShnatonSupplierMixin, HujiObjectSupplier):
    """
    Supplies the exam info html for a course.
    """

    def __init__(self, course_id: str, year: int, **kwargs) -> None:
        super().__init__(**kwargs)
        self._course_id = course_id
        self._year = year
        self._html_to_exams = HtmlToExams()

    async def supply(self) -> List[Exam]:
        fetcher = ExamFetcher(self._course_id, self._year, self._session)
        print(f"Requesting exam {self._course_id}")
        soup = await fetcher.acollect()
        print(f"Got exam for {self._course_id}")
        return self._html_to_exams.convert(soup)
