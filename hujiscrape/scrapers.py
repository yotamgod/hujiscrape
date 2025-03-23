import asyncio
from typing import List

from tqdm.asyncio import tqdm

from fetch_tasks import CourseFetchTask
from fetchers import Fetcher
from html_to_object import HtmlToCourse, HtmlToExams
from huji_objects import Course


class ShnatonScraper:
    def __init__(self, fetcher: Fetcher | None = None) -> None:
        self._fetcher = fetcher or Fetcher()

    async def scrape(self, **kwargs):
        raise NotImplementedError()


class SingleCourseScraper(ShnatonScraper):
    MISSING_COURSE_TEXT = "לא נמצא קורס"

    def __init__(self, fetcher: Fetcher | None = None, allow_missing_courses: bool = False) -> None:
        """
        :param allow_missing_courses: should missing course requests result in an exception that stops the
                                      scraping process
        """
        super().__init__(fetcher)
        self._course_parser = HtmlToCourse()
        self._exam_parser = HtmlToExams()
        self._allow_missing_courses = allow_missing_courses

    async def scrape(
            self,
            course_ids: list[int | str],
            year: int,
            include_exams: bool = True,
            show_progress: bool = False
    ) -> List[Course]:
        as_completed_method = asyncio.as_completed if not show_progress else tqdm.as_completed
        courses = []

        async with self._fetcher:
            course_scrape_tasks = [
                self._scrape_single_course(CourseFetchTask(course_id, year, fetch_exam=include_exams))
                for course_id in course_ids
            ]

            for scrape_coro in as_completed_method(course_scrape_tasks):
                course = await scrape_coro
                if course is not None:
                    courses.append(course)

            return courses

    async def _scrape_single_course(self, course_fetch_task: CourseFetchTask) -> Course | None:
        # Request course from shnaton
        course_html = await self._fetcher.fetch(course_fetch_task)

        if self.MISSING_COURSE_TEXT in course_html:
            if not self._allow_missing_courses:
                raise ValueError(f"Course {course_fetch_task.course_id} not found in {course_fetch_task.year}")

            return None

        # Parse the html to a course
        try:
            course = self._course_parser.convert(course_html)
        except Exception:
            print(f'Failed to convert course {course_fetch_task.course_id}')
            raise

        # If the course has an exam task, add it as well.
        if course_fetch_task.exam_fetch_task is not None:
            exams_html = await self._fetcher.fetch(course_fetch_task.exam_fetch_task)
            exams = self._exam_parser.convert(exams_html)
            course.exams = exams

        return course
