from hujiscrape import Semester
from hujiscrape.html_to_object import *
from hujiscrape.huji_objects import *


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
        Lesson(location='פלדמן א', passing_type='15/11/23 , בקמפוס', time='15:45-15:00', day="יום ב'",
               semester=Semester.A, group='', type='', lecturers=[], row=0),
        Lesson(location='פלדמן ב (קרית א"י ספרא)', passing_type='באולם ומוקלט', time='18:45-18:00', day="יום א'",
               semester=Semester.A, group='(א)', type='שעור', lecturers=['ד"ר '], row=0),
        Lesson(location='פלדמן א (קרית א"י ספרא)', passing_type='באולם ומוקלט', time='15:45-14:00', day="יום א'",
               semester=Semester.A, group='(א)', type='שעור', lecturers=['ד"ר '], row=0),
        Lesson(location='פלדמן ב', passing_type='15/11/23 , בקמפוס', time='18:00-17:00', day="יום ב'",
               semester=Semester.A, group='', type='', lecturers=[], row=0),
        Lesson(location='פלדמן א (קרית א"י ספרא)', passing_type='באולם ומוקלט', time='15:45-14:00', day="יום ב'",
               semester=Semester.A, group='(א)', type='שעור', lecturers=['ד"ר '], row=0),
        Lesson(location='פלדמן א (קרית א"י ספרא)', passing_type='באולם ומוקלט', time='15:45-14:00', day="יום ג'",
               semester=Semester.A, group='(א)', type='שעור', lecturers=['ד"ר '], row=0),
        Lesson(location='פלדמן ב', passing_type='18/10/23 , בקמפוס', time='15:45-15:00', day="יום ב'",
               semester=Semester.A, group='', type='', lecturers=[], row=0),
        Lesson(location='פלדמן ג', passing_type='15/11/23 , בקמפוס', time='18:00-17:00', day="יום ב'",
               semester=Semester.A, group='', type='', lecturers=[], row=0),
        Lesson(location='פלדמן ב', passing_type='18/10/23 , בקמפוס', time='15:45-15:00', day="יום ב'",
               semester=Semester.B, group='', type='', lecturers=[], row=0),
        Lesson(location='פלדמן ב', passing_type='18/10/23 , בקמפוס', time='15:45-15:00', day="יום ב'",
               semester=Semester.AB, group='', type='', lecturers=[], row=0),
        Lesson(location='פלדמן א (קרית א"י ספרא)', passing_type='באולם ומוקלט', time='15:45-14:00', day="יום ב'",
               semester=Semester.Yearly, group='(א)', type='שעור', lecturers=['ד"ר '], row=0),
        Lesson(location='פלדמן א (קרית א"י ספרא)', passing_type='באולם ומוקלט', time='15:45-14:00', day="יום ד'",
               semester=Semester.A, group='(א)', type='שעור', lecturers=['ד"ר '], row=0),
        Lesson(location='פלדמן א (קרית א"י ספרא)', passing_type='באולם ומוקלט', time='14:45-14:00', day="יום ב'",
               semester=Semester.A, group='(א)', type='שעור', lecturers=['ד"ר '], row=0),
        Lesson(location='פלדמן א', passing_type='01/11/23 , בקמפוס', time='15:45-15:00', day="יום ב'",
               semester=Semester.A, group='', type='', lecturers=[], row=0),
    ]

    output = HtmlToCourse()._sort_lessons(lessons)
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
        Lesson(location='פלדמן א', passing_type='01/11/23 , בקמפוס', time='15:45-15:00', day="יום ב'",
               semester=Semester.A, group='', type='', lecturers=[], row=0),
        Lesson(location='פלדמן א', passing_type='15/11/23 , בקמפוס', time='15:45-15:00', day="יום ב'",
               semester=Semester.A, group='', type='', lecturers=[], row=0),

        # Note: this is here because the ordering is done textually.
        Lesson(location='פלדמן ב', passing_type='18/10/23 , בקמפוס', time='15:45-15:00', day="יום ב'",
               semester=Semester.A, group='', type='', lecturers=[], row=0),

        Lesson(location='פלדמן ב', passing_type='15/11/23 , בקמפוס', time='18:00-17:00', day="יום ב'",
               semester=Semester.A, group='', type='', lecturers=[], row=0),
        Lesson(location='פלדמן ג', passing_type='15/11/23 , בקמפוס', time='18:00-17:00', day="יום ב'",
               semester=Semester.A, group='', type='', lecturers=[], row=0),
        Lesson(location='פלדמן א (קרית א"י ספרא)', passing_type='באולם ומוקלט', time='15:45-14:00', day="יום ג'",
               semester=Semester.A, group='(א)', type='שעור', lecturers=['ד"ר '], row=0),
        Lesson(location='פלדמן א (קרית א"י ספרא)', passing_type='באולם ומוקלט', time='15:45-14:00', day="יום ד'",
               semester=Semester.A, group='(א)', type='שעור', lecturers=['ד"ר '], row=0),
        Lesson(location='פלדמן א (קרית א"י ספרא)', passing_type='באולם ומוקלט', time='14:45-13:00', day="יום ה'",
               semester=Semester.A, group='(א)', type='שעור', lecturers=['ד"ר '], row=0),
        Lesson(location='פלדמן א (קרית א"י ספרא)', passing_type='באולם ומוקלט', time='15:45-14:00', day="יום ה'",
               semester=Semester.A, group='(א)', type='שעור', lecturers=['ד"ר '], row=0),
        Lesson(location='פלדמן ב', passing_type='18/10/23 , בקמפוס', time='15:45-15:00', day="יום ב'",
               semester=Semester.B, group='', type='', lecturers=[], row=0),
        Lesson(location='פלדמן ב', passing_type='18/10/23 , בקמפוס', time='15:45-15:00', day="יום ב'",
               semester=Semester.AB, group='', type='', lecturers=[], row=0),
        Lesson(location='פלדמן א (קרית א"י ספרא)', passing_type='באולם ומוקלט', time='15:45-14:00', day="יום ב'",
               semester=Semester.Yearly, group='(א)', type='שעור', lecturers=['ד"ר '], row=0),
    ]
