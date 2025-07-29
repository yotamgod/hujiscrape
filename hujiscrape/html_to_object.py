import re
from typing import Union, List

from bs4 import BeautifulSoup, Tag, NavigableString

from hujiscrape.huji_objects import HujiObject, Lesson, Course, Exam

Bs4Obj = Union[BeautifulSoup, Tag, NavigableString]


class HtmlToObject:
    """
    Object that receives specific html and converts it to a huji object
    """

    def convert(self, html_str: str) -> HujiObject:
        raise NotImplementedError()


class HtmlToCourse(HtmlToObject):

    def _sort_lessons(self, lessons: List[Lesson]) -> List[Lesson]:
        """
        Returns a sorted copy of a list of lessons by semester, day, time, and other fields, to preserve the same
        order between different runs of the program.
        :param lessons: list of lessons
        :return: sorted list of lessons
        """
        return sorted(lessons, key=lambda lesson: (lesson.semester, lesson.day, lesson.start_time, lesson.end_time,
                                                   lesson.passing_type, lesson.location))

    def convert(self, html_str: str) -> Course:
        html = BeautifulSoup(html_str, 'html.parser')

        # Extract faculty and department
        faculty_data = html.find('div', class_='data-school').text.strip()
        faculty_parts = faculty_data.split(':')
        faculty = faculty_parts[0].strip()
        department = faculty_parts[1].strip() if len(faculty_parts) > 1 else ""

        # Extract course details from the title section
        course_id = html.find('div', class_='title').text.strip().split()[-1]
        hebrew_course_name = html.find('div', class_='subtitle').text.strip()
        english_course_name = html.find('div', class_='subtitle-eng').text.strip()

        # Extract additional data
        additional_data = html.find('div', class_='additional-data')
        semester = additional_data.find('div', class_='additional-data-semester').text.strip()
        # semester = Semester.from_hebrew(semester_text)

        weekly_hours_div = additional_data.find('div', class_='.additional-data-points')
        weekly_hours = int(re.search(r'\d+', weekly_hours_div.text.strip()).group()) if weekly_hours_div else 0

        credits_text = additional_data.find('div', class_='additional-data-student-points').text.strip()
        credit_points = int(re.search(r'\d+', credits_text).group())

        # Get test information
        test_div = additional_data.find('div', class_='additional-data-test')
        test_info = test_div.text.strip() if test_div else ""
        exam_type = test_info
        exam_length = 0
        if re.search(r'(\d+\.\d+)', test_info):
            exam_length = float(re.search(r'(\d+\.\d+)', test_info).group())

        # Get language
        language_div = additional_data.find('div', class_='additional-data-language')
        language = language_div.text.strip() if language_div else ""

        is_running = True  # Assuming course is running if it's in the system

        # Extract notes
        notes_div = html.find('div', id='comments-course-NumCourse')
        hebrew_notes = notes_div.text.strip() if notes_div else ""
        english_notes = ""  # Not found in the new format

        # Extract syllabus and moodle links
        syllabus_url = ""
        moodle_url = ""

        cyllabus_tag = html.select_one(".cyllabus-cource")
        if cyllabus_tag and "href" in cyllabus_tag.attrs:
            href = cyllabus_tag["href"]
            # Extract the URL from JavaScript function
            if "javascript:OpenUrl(" in href:
                url_parts = href.split("'")
                if len(url_parts) >= 2:
                    syllabus_url = f"https://shnaton.huji.ac.il{url_parts[1]}"

        moodle_tag = html.select_one(".moodle-cource")
        if moodle_tag and "href" in moodle_tag.attrs:
            moodle_url = moodle_tag["href"]

        # Extract schedule information
        schedule = []
        rows = html.find_all('div', class_='row')

        # Skip the title row
        for row_num, row in enumerate(rows[1:], 0):
            lecturer_name_div = row.find('div', class_='lecturer-name')
            lecturers = []
            if lecturer_name_div and lecturer_name_div.text.strip():
                lecturers = [line for line in lecturer_name_div.stripped_strings]

            # Get groups, semester, days, hours, lesson types
            groups = [group.text for group in row.find('div', class_='groups').find_all('div')] if row.find('div',
                                                                                                            class_='groups') else []
            semesters = [sem.text for sem in row.find('div', class_='semester').find_all('div')] if row.find('div',
                                                                                                             class_='semester') else []
            days = [day.text.strip() for day in row.find('div', class_='days').find_all('div', class_='day')] if row.find('div',
                                                                                                                  class_='days') else []
            hours = [hour.text for hour in row.find('div', class_='hour').find_all('div') if
                     hour.text.strip()] if row.find('div', class_='hour') else []
            lesson_types = [lesson.text for lesson in row.find('div', class_='lesson').find_all('div')] if row.find(
                'div', class_='lesson') else []
            places = [place.text.strip() for place in
                      row.find('div', class_='places').find_all('div', class_='place-item')] if row.find('div',
                                                                                                         class_='places') else []
            notes = [note.text.strip() for note in row.find('div', class_='note').find_all('div') if
                     note.text.strip()] if row.find('div', class_='note') else []

            # Create lesson objects
            max_items = max(len(semesters), len(days), len(hours), len(places))

            for i in range(max_items):
                group = groups[0] if groups else ""
                lesson_type = lesson_types[0] if lesson_types else ""
                semester_val = semesters[i] if i < len(semesters) else ""
                day_val = days[i] if i < len(days) else ""
                time_val = hours[i] if i < len(hours) else ""
                location_val = places[i] if i < len(places) else ""
                passing_type_val = notes[i] if i < len(notes) else ""

                lesson = Lesson(
                    location=location_val,
                    passing_type=passing_type_val,
                    time=time_val,
                    day=day_val,
                    semester=semester_val,
                    group=group,
                    type=lesson_type,
                    lecturers=lecturers,
                    row=row_num
                )
                schedule.append(lesson)

        # Sort the schedule
        schedule = self._sort_lessons(schedule)

        return Course(
            faculty=faculty,
            department=department,
            course_id=course_id,
            english_name=english_course_name,
            hebrew_name=hebrew_course_name,
            credits=credit_points,
            weekly_hours=weekly_hours,
            semester=semester,
            language=language,
            exam_length=exam_length,
            exam_type=exam_type,
            schedule=schedule,
            exams=None,  # We'll need to handle exams separately
            hebrew_notes=hebrew_notes,
            english_notes=english_notes,
            is_running=is_running,
            syllabus_url=syllabus_url,
            moodle_url=moodle_url
        )


class HtmlToExams(HtmlToObject):
    def convert(self, html_str: str) -> List[Exam]:
        html = BeautifulSoup(html_str, 'html.parser')
        exam_table = html.find('table')
        exams = []
        for tr in exam_table.find_all('tr')[1:]:
            semester, moed, exam_date, exam_hour, location, exam_notes = [td.text for td in tr.find_all('td')]
            exams.append(
                Exam(exam_date, exam_hour, exam_notes, location, moed, semester)
            )
        return exams
