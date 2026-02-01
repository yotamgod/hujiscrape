import asyncio
import os
import time
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from typing import List, Tuple

from tqdm.asyncio import tqdm

from hujiscrape.fetch_tasks import CourseFetchTask, ExamFetchTask
from hujiscrape.fetchers import Fetcher
from hujiscrape.html_to_object import HtmlToCourse, HtmlToExams
from hujiscrape.huji_objects import Course


def _cpu_bound_parse_course(parser: HtmlToCourse, html: str) -> Tuple[Course, float]:
    """
    Runs in a separate process.
    Returns: (Course Object, Execution Time in Seconds)
    """
    t_start = time.time()
    course = parser.convert(html)
    duration = time.time() - t_start
    return course, duration


class ShnatonScraper:
    def __init__(self, fetcher: Fetcher | None = None) -> None:
        self._fetcher = fetcher or Fetcher()

    async def scrape(self, **kwargs):
        raise NotImplementedError()


class SingleCourseScraper(ShnatonScraper):
    MISSING_COURSE_TEXT = "לא נמצא קורס"
    MAX_HTML_SIZE = 5 * 1024 * 1024  # 5 MB
    LONG_PARSE_THRESHOLD = 5.0  # seconds

    def __init__(
            self, fetcher: Fetcher | None = None, max_cpu_workers: int | None = None
    ) -> None:
        """
        :param max_cpu_workers: Number of CPU processes. If None, uses os.cpu_count().
        """
        super().__init__(fetcher)
        self._course_parser = HtmlToCourse()
        self._exam_parser = HtmlToExams()

        self._workers = max_cpu_workers or os.cpu_count() or 1
        self._pool = ProcessPoolExecutor(max_workers=self._workers)

    async def scrape(
            self,
            course_ids: list[int | str],
            year: int,
            include_exams: bool = True,
            show_progress: bool = False,
            fail_after_n_missing_courses: int = 0,
    ) -> List[Course]:
        courses = []
        failed_courses = 0

        async with self._fetcher:
            course_scrape_tasks = [
                self._scrape_single_course(CourseFetchTask(course_id, year))
                for course_id in course_ids
            ]

            await_for_courses = (
                asyncio.as_completed
                if not show_progress
                else partial(tqdm.as_completed, desc="Scraping courses")
            )

            try:
                for course_coro in await_for_courses(course_scrape_tasks):
                    course = await course_coro
                    if course is None:
                        failed_courses += 1
                        if (
                                fail_after_n_missing_courses
                                and failed_courses >= fail_after_n_missing_courses
                        ):
                            raise ValueError(
                                f"Failed to fetch {failed_courses} courses"
                            )
                        continue

                    courses.append(course)

                if include_exams:
                    exam_scrape_tasks = [
                        self._attach_exams_to_course(course, year) for course in courses
                    ]

                    await_for_exams = (
                        asyncio.as_completed
                        if not show_progress
                        else partial(tqdm.as_completed, desc="Scraping exams")
                    )
                    for exams_coro in await_for_exams(exam_scrape_tasks):
                        await exams_coro

            finally:
                # Cleanup processes gracefully
                self._pool.shutdown(wait=False)

            return courses

    async def _scrape_single_course(
            self, course_fetch_task: CourseFetchTask
    ) -> Course | None:
        # Download course HTML
        try:
            course_html = await self._fetcher.fetch(course_fetch_task)
        except Exception:
            return None

        # Filter out missing or too large courses before parsing
        if not course_html or self.MISSING_COURSE_TEXT in course_html:
            return None
        if len(course_html) > self.MAX_HTML_SIZE:
            tqdm.write(
                f"[SKIP] Course {course_fetch_task.course_id} is too large "
                f"({len(course_html) / 1024 / 1024:.2f} MB). Skipping parse."
            )
            return None

        # Parse course HTML in separate process to avoid blocking event loop
        try:
            loop = asyncio.get_running_loop()

            # Run in process, receive (Result, Duration) tuple back
            course, duration = await loop.run_in_executor(
                self._pool, _cpu_bound_parse_course, self._course_parser, course_html
            )

            # Check actual CPU time, not queue wait time
            if duration > self.LONG_PARSE_THRESHOLD:
                tqdm.write(
                    f"[WARNING] Slow Parse: Course {course_fetch_task.course_id} took {duration:.2f}s"
                )

        except Exception as e:
            tqdm.write(f"[WARNING] Failed to convert course {course_fetch_task.course_id}: {e}")
            return None

        return course

    async def _attach_exams_to_course(self, course: Course, year: int) -> None:
        exams_html = await self._fetcher.fetch(ExamFetchTask(course.course_id, year))
        course.exams = self._exam_parser.convert(exams_html)
