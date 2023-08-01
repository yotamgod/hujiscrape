from dataclasses import dataclass
from typing import List, Tuple


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
    is_running: bool

    def __hash__(self) -> int:
        return int(self.course_id)

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Course):
            return False

        return self.course_id == o.course_id


class Exam(HujiObject):
    date: str
    hour: str
    notes: str
    location: str
    moed: str
    semester: str
