import asyncio
import re
from typing import Any, List, Dict, AsyncIterator, Tuple

import aiohttp

from collectors import ShantonCourseFetcher, MaslulFetcher, ExamFetcher
from html_to_object import HtmlToCourse, HtmlToExams
from huji_objects import Course, Exam
from magics import Toar, ToarYear


class HujiObjectSupplier:
    """
    Supplies Shnaton info as the HTML from a response.
    """

    async def supply(self) -> Any:
        raise NotImplementedError()


class AbstractCourseSupplier(HujiObjectSupplier):
    """
    Supplies a list of courses.
    """
    DEFAULT_SEMAPHORE_SIZE = 100

    def __init__(self, year: int, session: aiohttp.ClientSession = None, semaphore: asyncio.Semaphore = None,
                 include_exams=True) -> None:
        self._year = year
        self._session = session or aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=self.DEFAULT_SEMAPHORE_SIZE))
        self._semaphore = semaphore or asyncio.Semaphore(self.DEFAULT_SEMAPHORE_SIZE)
        self._include_exams = include_exams

    async def supply(self) -> List[Course]:
        courses = []

        # Add exams to courses if needed
        exam_tasks = []

        # with asyncio.TaskGroup() as tg:
        async for course in self._supply():  # ToDO: check how to iterate an async iterator
            courses.append(course)

            if self._include_exams:
                exam_tasks.append(
                    asyncio.create_task(self._add_exams([course]))
                )
        await asyncio.gather(*exam_tasks)
        # courses = await self._supply()
        #
        # if not self._include_exams:
        #     return courses
        #
        # Add the exams to the courses
        # await self._add_exams(courses)
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
        exam_tasks = [asyncio.create_task(coro) for coro in exam_coros]
        results: List[List[Exam]] = await asyncio.gather(*exam_tasks)
        for idx, result in enumerate(results):
            courses[idx].exams = result

    async def _get_exams(self, course: Course):
        """
        Returns the exams for a specific course.
        :param course:
        :return:
        """
        exam_supplier = ExamSupplier(course.course_id, self._year, self._session)
        # async with self._semaphore:
        return await exam_supplier.supply()


class CourseSupplier(AbstractCourseSupplier):
    """
    Returns the direct html table containing a course's information.
    """

    def __init__(self, course_ids: List[str], year: int, session: aiohttp.ClientSession = None,
                 semaphore: asyncio.Semaphore = None, include_exams=True) -> None:
        super().__init__(year, session, semaphore, include_exams)
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


class MaslulPageSupplier(AbstractCourseSupplier):

    def __init__(self, year: int, faculty: str, hug: str, maslul: str, toar: Toar = Toar.Any,
                 toar_year: ToarYear = ToarYear.Any, page: int = 1, include_exams=True,
                 session: aiohttp.ClientSession = None, semaphore: asyncio.Semaphore = None) -> None:
        super().__init__(year, session, semaphore, include_exams)
        self._faculty = faculty
        self._hug = hug
        self._maslul = maslul
        self._toar = toar
        self._toar_year = toar_year
        self._page = page
        self._html_to_course = HtmlToCourse()

    async def _supply(self) -> AsyncIterator[Course]:
        fetcher = MaslulFetcher(self._year, self._faculty, self._hug, self._maslul, self._toar, self._toar_year,
                                self._page, self._session)
        # import time
        # before = time.time()
        soup = await fetcher.acollect()
        # print(f"After page request: {time.time() - before}")
        course_tds = [div.parent for div in soup.find_all('div', class_='courseTitle')]
        courses = (self._html_to_course.convert(td) for td in course_tds)
        for course in courses:
            yield course

    def next_page_supplier(self) -> 'MaslulPageSupplier':
        """
        Returns a new supplier object of the next page.
        """
        return MaslulPageSupplier(self._year, self._faculty, self._hug, self._maslul, self._toar, self._toar_year,
                                  self._page + 1, self._include_exams, self._session, self._semaphore)


class MaslulAllPageSupplier(AbstractCourseSupplier):

    def __init__(self, year: int, faculty: str, hug: str, maslul: str, toar: Toar = Toar.Any,
                 toar_year: ToarYear = ToarYear.Any, include_exams=True,
                 session: aiohttp.ClientSession = None, semaphore: asyncio.Semaphore = None) -> None:
        super().__init__(year, session, semaphore, include_exams)
        self._faculty = faculty
        self._hug = hug
        self._maslul = maslul
        self._toar = toar
        self._toar_year = toar_year

    # def __init__(self, year: int, faculty: str, hug: str, maslul: str, toar: Toar = Toar.Any,
    #              toar_year: ToarYear = ToarYear.Any, session: aiohttp.ClientSession = None,
    #              concurrent_requests: int = 10) -> None:
    #     self._session = session or aiohttp.ClientSession(connector=aiohttp.TCPConnector(force_close=True))
    #     self._semaphore = asyncio.Semaphore(concurrent_requests)
    #     self._year = year
    #     self._faculty = faculty
    #     self._hug = hug
    #     self._maslul = maslul
    #     self._toar = toar
    #     self._toar_year = toar_year
    #
    #     # Using a fetcher to find the number of pages to download
    #     self._page_1_maslul_fetcher = MaslulFetcher(year, faculty, hug, maslul, toar, toar_year, 1,
    #                                                 session=self._session)

    async def _get_page_bounds(self) -> Tuple[int, int]:
        fetcher = MaslulFetcher(self._year, self._faculty, self._hug, self._maslul, self._toar,
                                self._toar_year, 1, self._session)
        soup = await fetcher.acollect()
        page_info_text = soup.find('div', class_='facultyTitle').find_next('td').text.strip()

        if not page_info_text:  # Happens if there is only a single page
            return 1, 1
        from_page, to_page = [int(number) for number in re.findall(r'\d+', page_info_text)]
        return from_page, to_page

    async def _supply(self) -> AsyncIterator[Course]:
        # Collect the first page to find out the number of pages required
        page_from, page_to = await self._get_page_bounds()
        course_ids = set()

        # TODO: First page will be collected twice, can fix this
        page_supplier_coros = [self._collect_page(page) for page in range(page_from, page_to + 1)]
        # page_supplier_tasks = [asyncio.create_task(coro) for coro in page_supplier_coros]
        for task in asyncio.as_completed(page_supplier_coros):
            course_list = await task

            # Yield only unique courses
            new_courses = [course for course in course_list if course.course_id not in course_ids]
            for course in new_courses:
                course_ids.add(course.course_id)
                yield course

        # results: List[List[Course]] = await asyncio.gather(*page_supplier_tasks)  # TODO: handle errors.

        # Flatten the list of lists of courses, and dedup the courses before returning the list
        # id_to_course = {course.course_id: course for course_list in results for course in course_list}
        # return [course for course in id_to_course.values()]

    async def _collect_page(self, page: int) -> List[Course]:
        """
        Collects a page using the MaslulPageSupplier
        :param page: page to download
        :return: a list of courses
        """
        # Only include exams as a part of the current supplier (so they are not added twice).
        supplier = MaslulPageSupplier(self._year, self._faculty, self._hug, self._maslul,
                                      self._toar, self._toar_year, page, session=self._session, include_exams=False)

        # async with self._semaphore:
        print(f"Requesting page: {page}")
        course_list = await supplier.supply()
        print(f"Page got: {page}")
        return course_list
        # for course in await supplier.supply():
        #     yield course


class ExamSupplier(HujiObjectSupplier):
    """
    Supplies the exam info html for a course.
    """
    DEFAULT_SEMAPHORE_SIZE = 100

    def __init__(self, course_id: str, year: int, session: aiohttp.ClientSession = None,
                 semaphore: asyncio.Semaphore = None) -> None:
        self._course_id = course_id
        self._year = year
        self._session = session or aiohttp.ClientSession()
        self._semaphore = semaphore or asyncio.Semaphore(self.DEFAULT_SEMAPHORE_SIZE)
        # self._exam_fetcher = ExamFetcher(course_id, year, session)
        self._html_to_exams = HtmlToExams()

    async def supply(self) -> List[Exam]:
        fetcher = ExamFetcher(self._course_id, self._year, self._session)
        print(f"Requesting exam {self._course_id}")
        soup = await fetcher.acollect()
        print(f"Got exam for {self._course_id}")
        return self._html_to_exams.convert(soup)
