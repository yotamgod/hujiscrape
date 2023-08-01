import re
from typing import Union, List

from bs4 import BeautifulSoup, Tag, NavigableString

from huji_objects import HujiObject, Lesson, Course
from magics import PASSING_TYPE_IDX, LOCATION_IDX, TIME_IDX, DAY_IDX, SEMESTER_IDX, GROUP_IDX, LESSON_TYPE_IDX, \
    LECTURER_IDX

Bs4Obj = Union[BeautifulSoup, Tag, NavigableString]


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

        # Collect elements between <br> tags
        for content in td_tag.contents:

            if isinstance(content, NavigableString) and content.strip() != '':
                # If the content is a string and not just \t or \n, append it.
                text_list.append(content.strip())
                continue

            # If the content is a span, the correct value will either be in a <b> or the text itself
            if getattr(content, 'name') == 'span':
                content: Tag
                # Second value in contents will be a NavigableString. If this doesn't include ... it is the correct one.
                if '...' in content.contents[1].text:
                    text_list.append(content.find_next('b').text.strip())
                else:
                    text_list.append(content.contents[1].text.strip())
                continue

            if getattr(content, 'name') == 'b':
                text_list.append(content.text.strip())
                continue

            # Otherwise we aren't interested
            continue
        return text_list

    def _extract_lesson_locations(self, td_tag: Tag):
        pass

    def convert(self, html: Bs4Obj) -> Course:
        faculty_div = html.find('div', class_='courseTitle')
        faculty = faculty_div.text.strip()
        course_table = faculty_div.find_next('table')
        print([b.text.strip() for b in course_table.find_all('b')])
        # If the course isn't running this year, there will be a red <b> tag here
        english_course_name, hebrew_course_name, course_id = [b.text.strip() for b in course_table.find_all('b') if
                                                              b.parent.name != 'font']
        is_running = course_table.find('font', attrs={'color': 'red'}) is None

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

            # Assume that the number of lessons in each group is equal to the number of locations
            num_lessons = len(lesson_data_lists[0])

            # Pad lists with empty strings to match the number of lessons
            for idx in range(LOCATION_IDX, SEMESTER_IDX + 1):
                lesson_data_lists[idx] += [''] * (num_lessons - len(lesson_data_lists[idx]))

            # Create lessons
            for lesson_idx in range(num_lessons):
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
                        lesson_data_lists[LECTURER_IDX]
                    )
                )

        hebrew_note, english_note = [row.find_next('td').text.strip() for row in note_rows] if note_rows else ['', '']
        return Course(faculty, course_id, english_course_name, hebrew_course_name, points, semester, language,
                      test_length, test_type, schedule, hebrew_note, english_note, is_running)
