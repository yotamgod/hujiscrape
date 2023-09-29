from html_to_object import *
from huji_objects import *


def test_sorting_list_of_lessons():
    """
    Test that lessons are sorted correctly in the HtmlToCourse._sort_lessons_by_day_and_time method, according to day,
    start time and end time.
    """

    lessons = [
        Lesson(location='פלדמן א (קרית א"י ספרא)', passing_type='באולם ומוקלט', time='15:45-14:00', day="יום ה'",
               semester=Semester.A, group='(א)', type='שעור', lecturers=['ד"ר '], row=0),
        Lesson(location='פלדמן א (קרית א"י ספרא)', passing_type='באולם ומוקלט', time='14:45-13:00', day="יום ה'",
               semester=Semester.A, group='(א)', type='שעור', lecturers=['ד"ר '], row=0),
        Lesson(location='פלדמן א (קרית א"י ספרא)', passing_type='באולם ומוקלט', time='13:45-12:00', day="יום ב'",
               semester=Semester.A, group='(א)', type='שעור', lecturers=['ד"ר '], row=0),
        Lesson(location='פלדמן ב (קרית א"י ספרא)', passing_type='באולם ומוקלט', time='18:45-18:00', day="יום א'",
               semester=Semester.A, group='(א)', type='שעור', lecturers=['ד"ר '], row=0),
        Lesson(location='פלדמן א (קרית א"י ספרא)', passing_type='באולם ומוקלט', time='15:45-14:00', day="יום א'",
               semester=Semester.A, group='(א)', type='שעור', lecturers=['ד"ר '], row=0),
        Lesson(location='פלדמן א (קרית א"י ספרא)', passing_type='באולם ומוקלט', time='15:45-14:00', day="יום ב'",
                semester=Semester.A, group='(א)', type='שעור', lecturers=['ד"ר '], row=0),
        Lesson(location='פלדמן א (קרית א"י ספרא)', passing_type='באולם ומוקלט', time='15:45-14:00', day="יום ג'",
                semester=Semester.A, group='(א)', type='שעור', lecturers=['ד"ר '], row=0),
        Lesson(location='פלדמן א (קרית א"י ספרא)', passing_type='באולם ומוקלט', time='15:45-14:00', day="יום ד'",
                semester=Semester.A, group='(א)', type='שעור', lecturers=['ד"ר '], row=0),
        Lesson(location='פלדמן א (קרית א"י ספרא)', passing_type='באולם ומוקלט', time='14:45-14:00', day="יום ב'",
               semester=Semester.A, group='(א)', type='שעור', lecturers=['ד"ר '], row=0),
    ]

    output = HtmlToCourse()._sort_lessons_by_day_and_time(lessons)
    assert output == [
        Lesson(location='פלדמן א (קרית א"י ספרא)', passing_type='באולם ומוקלט', time='15:45-14:00', day="יום א'",
               semester=Semester.A, group='(א)', type='שעור', lecturers=['ד"ר '], row=0),
        Lesson(location='פלדמן ב (קרית א"י ספרא)', passing_type='באולם ומוקלט', time='18:45-18:00', day="יום א'",
                semester=Semester.A, group='(א)', type='שעור', lecturers=['ד"ר '], row=0),
        Lesson(location='פלדמן א (קרית א"י ספרא)', passing_type='באולם ומוקלט', time='13:45-12:00', day="יום ב'",
                semester=Semester.A, group='(א)', type='שעור', lecturers=['ד"ר '], row=0),
        Lesson(location='פלדמן א (קרית א"י ספרא)', passing_type='באולם ומוקלט', time='14:45-14:00', day="יום ב'",
                semester=Semester.A, group='(א)', type='שעור', lecturers=['ד"ר '], row=0),
        Lesson(location='פלדמן א (קרית א"י ספרא)', passing_type='באולם ומוקלט', time='15:45-14:00', day="יום ב'",
                semester=Semester.A, group='(א)', type='שעור', lecturers=['ד"ר '], row=0),
        Lesson(location='פלדמן א (קרית א"י ספרא)', passing_type='באולם ומוקלט', time='15:45-14:00', day="יום ג'",
                semester=Semester.A, group='(א)', type='שעור', lecturers=['ד"ר '], row=0),
        Lesson(location='פלדמן א (קרית א"י ספרא)', passing_type='באולם ומוקלט', time='15:45-14:00', day="יום ד'",
                semester=Semester.A, group='(א)', type='שעור', lecturers=['ד"ר '], row=0),
        Lesson(location='פלדמן א (קרית א"י ספרא)', passing_type='באולם ומוקלט', time='14:45-13:00', day="יום ה'",
               semester=Semester.A, group='(א)', type='שעור', lecturers=['ד"ר '], row=0),
        Lesson(location='פלדמן א (קרית א"י ספרא)', passing_type='באולם ומוקלט', time='15:45-14:00', day="יום ה'",
                semester=Semester.A, group='(א)', type='שעור', lecturers=['ד"ר '], row=0)
    ]
