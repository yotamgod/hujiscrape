import asyncio
import logging
from functools import partial
from typing import List

from tqdm.asyncio import tqdm

from hujiscrape.fetch_tasks import CourseFetchTask, ExamFetchTask
from hujiscrape.fetchers import Fetcher
from hujiscrape.html_to_object import HtmlToCourse, HtmlToExams
from hujiscrape.huji_objects import Course


class ShnatonScraper:
    def __init__(self, fetcher: Fetcher | None = None) -> None:
        self._fetcher = fetcher or Fetcher()

    async def scrape(self, **kwargs):
        raise NotImplementedError()


class SingleCourseScraper(ShnatonScraper):
    MISSING_COURSE_TEXT = "לא נמצא קורס"

    def __init__(self, fetcher: Fetcher | None = None) -> None:
        """
        :param allow_missing_courses: should missing course requests result in an exception that stops the
                                      scraping process
        """
        super().__init__(fetcher)
        self._course_parser = HtmlToCourse()
        self._exam_parser = HtmlToExams()

    async def scrape(
            self,
            course_ids: list[int | str],
            year: int,
            include_exams: bool = True,
            show_progress: bool = False,
            fail_after_n_missing_courses: int = 0
    ) -> List[Course]:
        """
        Scrape multiple courses from shnaton
        :param course_ids: list of course ids to scrape
        :param year: year to scrape
        :param include_exams: should the exams be scraped as well
        :param show_progress: should a progress bar be shown
        :param fail_after_n_missing_courses: if more than n courses are missing, raise an exception.
                                             if 0, do not raise an exception
        :return: list of courses
        """
        courses = []
        failed_courses = 0

        async with self._fetcher:
            course_scrape_tasks = [
                self._scrape_single_course(CourseFetchTask(course_id, year))
                for course_id in course_ids
            ]

            await_for_courses = asyncio.as_completed if not show_progress else partial(tqdm.as_completed,
                                                                                       desc="Scraping courses")
            for course_coro in await_for_courses(course_scrape_tasks):
                course = await course_coro
                if course is None:
                    failed_courses += 1
                    if fail_after_n_missing_courses and failed_courses >= fail_after_n_missing_courses:
                        raise ValueError(f"Failed to fetch {failed_courses} courses")
                    continue

                courses.append(course)

            if include_exams:
                exam_scrape_tasks = [
                    self._attach_exams_to_course(course, year)
                    for course in courses
                ]

                # Separate await so that there is a progress bar for each
                await_for_exams = asyncio.as_completed if not show_progress else partial(tqdm.as_completed,
                                                                                         desc="Scraping exams")
                for exams_coro in await_for_exams(exam_scrape_tasks):
                    await exams_coro

            return courses

    async def _scrape_single_course(self, course_fetch_task: CourseFetchTask) -> Course | None:
        # Request course from shnaton
        course_html = await self._fetcher.fetch(course_fetch_task)

        if self.MISSING_COURSE_TEXT in course_html:
            logging.info(f"\nCourse {course_fetch_task.course_id} not found in {course_fetch_task.year}")

            return None

        # Parse the html to a course
        try:
            course = self._course_parser.convert(course_html)
        except Exception:
            print(f'Failed to convert course {course_fetch_task.course_id}')
            raise

        # If the course has an exam task, add it as well.
        # if course_fetch_task.exam_fetch_task is not None:
        #     exams_html = await self._fetcher.fetch(course_fetch_task.exam_fetch_task)
        #     exams = self._exam_parser.convert(exams_html)
        #     course.exams = exams

        return course

    async def _attach_exams_to_course(self, course: Course, year: int) -> None:
        exams_html = await self._fetcher.fetch(ExamFetchTask(course.course_id, year))
        course.exams = self._exam_parser.convert(exams_html)
