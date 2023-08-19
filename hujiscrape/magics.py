import enum
from typing import Optional


class Prisa(enum.IntEnum):
    Minimal = 0
    Medium = 1
    Maximal = 2


# Type of degree
class Toar(enum.IntEnum):
    Any = 0
    Boger = 1


# Year in the toar
class ToarYear(enum.IntEnum):
    Any = 0
    First = 1
    Second = 2
    Third = 3
    Fourth = 4


# Semesters
class Semester(enum.IntEnum):
    """
    Numbers correlate to values used to filter in the Shnaton
    """
    # TODO: might need to change this to just a normal enum
    A = 1
    B = 2
    AB = 3
    Summer = 5
    Yearly = 9

    def __str__(self):
        return self.name

    @classmethod
    def from_hebrew(cls, text: str) -> Optional['Semester']:
        """
        A method that returns an enum value for a given text.
        :return: an enum
        :raise: ValueError if the text doesn't map to any enum.
        """
        semester = {
            "סמסטר א": Semester.A,
            "סמסטר א'": Semester.A,
            "סמסטר ב": Semester.B,
            "סמסטר ב'": Semester.B,
            "סמסטר א' או/ו ב'": Semester.AB,
            "קיץ": Semester.Summer,
            "סמסטר קיץ": Semester.Summer,
            "שנתי": Semester.Yearly,
        }.get(text.strip())

        if semester is None:
            raise ValueError(f"'{text}' is not a valid Semester")

        return semester


# Lesson table indexes
LOCATION_IDX = 0
PASSING_TYPE_IDX = 1
TIME_IDX = 2
DAY_IDX = 3
SEMESTER_IDX = 4
GROUP_IDX = 5
LESSON_TYPE_IDX = 6
LECTURER_IDX = 7

if __name__ == '__main__':
    a = Semester("סמסטר א'")
    print(a)
