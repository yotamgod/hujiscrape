import asyncio
import re
import traceback
from asyncio import as_completed
from typing import Any, List, AsyncIterator, Tuple, Set, Generator, Optional

import aiohttp
from bs4 import BeautifulSoup
from tqdm.asyncio import tqdm

from hujiscrape.collectors import ShantonCourseFetcher, ExamFetcher
from hujiscrape.html_to_object import HtmlToCourse, HtmlToExams
from hujiscrape.huji_objects import Course, Exam


class HujiObjectScraper:
    """
    Scrapes Huji objects as the HTML from a response.
    """

    async def scrape(self) -> Any:
        raise NotImplementedError()

    async def __aenter__(self) -> 'HujiObjectScraper':
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class SessionScraperMixin:

    def __init__(self, *args, session: aiohttp.ClientSession = None, **kwargs) -> None:
        self._session = session or aiohttp.ClientSession()
        super().__init__(*args, **kwargs)

    async def __aenter__(self):
        await self._session.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._session.__aexit__(exc_type, exc_val, exc_tb)


class ShnatonScraperMixin(SessionScraperMixin):
    """
    A scraper for data from the shnaton.
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
            # connect is the timeout for getting a connection from the pool.
            timeout=aiohttp.ClientTimeout(connect=None),
            connector=aiohttp.TCPConnector(limit=concurrent_requests)
        )
        kwargs['session'] = session
        super().__init__(*args, **kwargs)


class AbstractShnatonCourseScraper(ShnatonScraperMixin, HujiObjectScraper):
    """
    Abstract class that scrapes a list of courses from the shnaton.
    Includes an option to add exams to output courses.
    """

    def __init__(self, year: int, include_exams: bool = True, show_progress: bool = False, **kwargs) -> None:

        super().__init__(**kwargs)
        self._year = year
        self._include_exams = include_exams
        self._show_progress = show_progress

    async def scrape(self) -> List[Course]:
        courses = []

        # Add exams to courses if needed
        exam_tasks = []

        async for course in self._scrape():
            courses.append(course)

            if self._include_exams:
                exam_tasks.append(
                    asyncio.create_task(self._add_exams([course]))
                )

        await asyncio.gather(*exam_tasks)
        return courses

    async def _scrape(self) -> AsyncIterator[Course]:
        raise NotImplementedError()

    async def _add_exams(self, courses: List[Course]):
        """
        A generic method to supply exams.
        :return:
        """

        exam_coros = [self._scrape_exams(course) for course in courses]
        results: List[List[Exam]] = await asyncio.gather(*exam_coros)
        for idx, result in enumerate(results):
            courses[idx].exams = result

    async def _scrape_exams(self, course: Course) -> List[Exam]:
        """
        Returns the exams for a specific course.
        :param course:
        :return:
        """
        exam_scraper = ExamScraper(course.course_id, self._year, session=self._session)
        return await exam_scraper.scrape()


class ShnatonByCourseIdScraper(AbstractShnatonCourseScraper):
    """
    Scrapes courses from shnaton by id.
    """

    def __init__(self, course_ids: List[str], year: int, include_exams=True, **kwargs) -> None:
        super().__init__(year=year, include_exams=include_exams, **kwargs)
        self._course_ids = course_ids
        self._html_to_course = HtmlToCourse()

    async def _scrape(self) -> AsyncIterator[Course]:
        coros = [self._fetch_course(course_id) for course_id in self._course_ids]
        as_completed_method = as_completed if not self._show_progress else tqdm.as_completed
        for task in as_completed_method(coros):
            course = await task
            if course is not None:
                yield course

    async def _fetch_course(self, course_id: str) -> Optional[Course]:
        """
        Returns a single course object.
        If the course is not found, returns None.
        :param course_id: course id to scrape
        :return: course object
        """
        fetcher = ShantonCourseFetcher(course_id, self._year, self._session)
        soup = await fetcher.afetch()
        if soup is None:
            return None

        try:
            course = self._html_to_course.convert(soup)
        except Exception as e:
            print(f'Failed to convert course {course_id}: {e}')
            traceback.print_exc()
            return None

        return course


class ExamScraper(ShnatonScraperMixin, HujiObjectScraper):
    """
    Scrapes the exam info html for a course.
    """

    def __init__(self, course_id: str, year: int, **kwargs) -> None:
        super().__init__(**kwargs)
        self._course_id = course_id
        self._year = year
        self._html_to_exams = HtmlToExams()

    async def scrape(self) -> List[Exam]:
        fetcher = ExamFetcher(self._course_id, self._year, self._session)
        soup = await fetcher.afetch()
        return self._html_to_exams.convert(soup)
