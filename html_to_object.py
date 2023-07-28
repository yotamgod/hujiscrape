import re
from typing import Union, List

from bs4 import BeautifulSoup, Tag, NavigableString

from huji_objects import HujiObject, Lesson, Course
from magics import PASSING_TYPE_IDX, LOCATION_IDX, TIME_IDX, DAY_IDX, SEMESTER_IDX, GROUP_IDX, LESSON_TYPE_IDX, \
    LECTURER_IDX

Bs4Obj = Union[BeautifulSoup, Tag]


class HtmlToObject:
    """
    Object that receives specific html and converts it to a huji object
    """

    def convert(self, html: Bs4Obj) -> HujiObject:
        raise NotImplementedError()


class HtmlToCourse(HtmlToObject):

    def _list_text_in_lesson_td(self, td_tag: Tag) -> List[str]:
        """
        Groups of lessons are in the same td and separated by <br> tags.
        This splits them all, returning the text in a list.
        Will never return an empty list (will return an empty string).
        :param td_tag: td tag to split
        """
        assert td_tag.attrs.get('class') == ['courseDet', 'text'], "Invalid tag for lesson data."
        text_list = []
        # There is a longer extraction sequence because of the lesson location
        for content in td_tag.contents:
            # If the content is a string and not just \t or \n, append it.
            if isinstance(content, NavigableString) and content.strip():
                text_list.append(content.strip())
                continue

            # If the content is a span, it will have a b element inside
            if getattr(content, 'name') == 'span':
                text_list.append(content.find_next('b').text.strip())
                continue

            if getattr(content, 'name') == 'b':
                text_list.append(content.text.strip())
                continue

            # Otherwise we aren't interested
            continue

        # Make sure we never get an empty list (always at least an empty string) to conform
        if not text_list:
            text_list.append('')

        return text_list

    def _extract_lesson_locations(self, td_tag: Tag):
        pass

    def convert(self, html: Bs4Obj) -> Course:
        faculty_div = html.find('div', class_='courseTitle')
        faculty = faculty_div.text.strip()
        course_table = faculty_div.find_next('table')
        english_course_name, hebrew_course_name, course_id = [b.text.strip() for b in course_table.find_all('b')]
        course_id = re.search(r'\d+', course_id).group()
        course_details_table = course_table.find_next('table')
        test_length, test_type, unknown_field, points, semester, language = [td.text.strip() for td in
                                                                             course_details_table.find_all('td')]
        details_table = html.find('div', id=re.compile('CourseDetails')).find_next('table')
        # First tr doesn't contain data, and last two are comments
        detail_rows = details_table.find_all('tr')[1:]
        schedule_rows, note_rows = detail_rows[:-2], detail_rows[-2:]
        schedule = []
        for row in schedule_rows:
            # Each row contains the information for a specific group and specific lesson type (targil, lecture..)
            lesson_tds = row.find_all('td')
            if not lesson_tds:
                continue

            # There can be multiple lessons embedded in the same row (same group)
            # Extract the text lists from each of the tds
            lesson_data_lists = [self._list_text_in_lesson_td(td) for td in lesson_tds]

            # There is an extra row for all fields of the lesson until the semester index
            for lesson_idx in range(len(lesson_data_lists[0])):
                schedule.append(
                    Lesson(
                        lesson_data_lists[LOCATION_IDX][lesson_idx],
                        lesson_data_lists[PASSING_TYPE_IDX][lesson_idx],
                        lesson_data_lists[TIME_IDX][lesson_idx],
                        lesson_data_lists[DAY_IDX][lesson_idx],
                        lesson_data_lists[SEMESTER_IDX][lesson_idx],
                        lesson_data_lists[GROUP_IDX][0],
                        lesson_data_lists[LESSON_TYPE_IDX][0],
                        # If there are no lecturers, return an empty list
                        lesson_data_lists[LECTURER_IDX] if lesson_data_lists[LECTURER_IDX][0] else []
                    )
                )

        hebrew_note, english_note = [row.find_next('td').text.strip() for row in note_rows]
        return Course(faculty, course_id, english_course_name, hebrew_course_name, points, semester, language,
                      test_length, test_type, schedule, hebrew_note, english_note)
