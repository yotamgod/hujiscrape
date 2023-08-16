import enum


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


# Lesson table indexes
LOCATION_IDX = 0
PASSING_TYPE_IDX = 1
TIME_IDX = 2
DAY_IDX = 3
SEMESTER_IDX = 4
GROUP_IDX = 5
LESSON_TYPE_IDX = 6
LECTURER_IDX = 7
