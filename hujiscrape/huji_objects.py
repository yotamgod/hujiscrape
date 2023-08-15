from dataclasses import dataclass
from typing import List, Optional


class HujiObject:
    pass


@dataclass(frozen=True)
class Lesson(HujiObject):
    location: str
    passing_type: str  # Meaning in campus / video taped etc...
    time: str
    day: str
    semester: str
    group: str
    type: str
    lecturers: List[str]


@dataclass(frozen=True)
class Exam(HujiObject):
    date: str
    hour: str
    notes: str
    location: str
    moed: str
    semester: str


@dataclass(frozen=False)
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
    exams: Optional[List[Exam]]
    hebrew_notes: str
    english_notes: str
    is_running: bool
