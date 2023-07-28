from dataclasses import dataclass
from typing import List


class HujiObject:
    pass


@dataclass
class Lesson(HujiObject):
    location: str
    passing_type: str  # Meaning in campus / video taped etc...
    time: str
    day: str
    semester: str
    group: str
    type: str
    lecturers: List[str]


@dataclass
class Course(HujiObject):
    faculty: str
    course_id: str
    english_name: str
    hebrew_name: str
    points: int
    semester: str
    language: str
    test_length: int
    test_type: str
    schedule: List[Lesson]
    hebrew_notes: str
    english_notes: str
