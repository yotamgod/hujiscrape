import re
from functools import partial
from typing import Any, Union, List

from bs4 import BeautifulSoup, Tag

from collectors import ShantonCourseFetcher, MaslulFetcher
from huji_objects import Course, Lesson
from magics import YEAR_ANY, TOAR_ANY

Bs4Obj = Union[BeautifulSoup, Tag]


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

    async def supply(self) -> Bs4Obj:
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

    async def supply(self) -> Course:
        soup = await self._course_fetcher.acollect()
        faculty_div = soup.find('div', class_='courseTitle')
        faculty = faculty_div.text.strip()
        course_table = faculty_div.find_next('table')
        english_course_name, hebrew_course_name, course_id = [b.text.strip() for b in course_table.find_all('b')]
        course_id = re.search(r'\d+', course_id).group()
        course_details_table = course_table.find_next('table')
        test_length, test_type, unknown_field, points, semesters, empty_field = [td.text.strip() for td in
                                                                                 course_details_table.find_all('td')]
        details_table = soup.find('div', id=re.compile('CourseDetails')).find_next('table')
        # First tr doesn't contain data, and last two are comments
        detail_rows = details_table.find_all('tr')[1:]
        schedule_rows, note_rows = detail_rows[:-2], detail_rows[-2:]
        schedule = []
        for row in schedule_rows:
            lesson_tds = row.find_all('td')
            if not lesson_tds:
                continue  # TODO: fix issue where there are multiple lectures in a single td
            lessons_in_group = len([tag for tag in lesson_tds[0].contents if getattr(tag, 'name', None) != 'br'])
            for idx in range(lessons_in_group):
                pass
            lecture_info: List[str] = [td.text.strip() for td in row.find_all('td')]


            schedule.append(
                Lesson(*lecture_info)
            )
        hebrew_note, english_note = [row.find_next('td').text.strip() for row in note_rows]
        return Course(faculty, course_id, english_course_name, hebrew_course_name, points, test_length, test_type,
                      schedule, hebrew_note, english_note)


class MaslulCourseSuppliers:

    def __init__(self, year: int, faculty: str, hug: str, maslul: str, toar: int = TOAR_ANY,
                 toar_year: int = YEAR_ANY) -> None:
        # Create a fetcher without a page set
        self._maslul_fetcher_partial = partial(MaslulFetcher, year=year, faculty=faculty, hug=hug, maslul=maslul,
                                               toar=toar, toar_year=toar_year)


class ExamSupplier(RawSupplier):
    """
    Supplies the exam info html for a course.
    """

    async def supply(self) -> Bs4Obj:
        raise NotImplementedError()
