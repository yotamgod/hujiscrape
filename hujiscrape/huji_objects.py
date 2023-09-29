from dataclasses import dataclass
from functools import cached_property
from typing import List, Optional, Tuple

from hujiscrape.magics import Semester


class HujiObject:
    pass


@dataclass(frozen=True)
class Lesson(HujiObject):
    location: str
    passing_type: str  # Meaning in campus / videotaped etc...
    time: str
    day: str
    semester: Semester
    group: str
    type: str  # Tirgul, Lecture...
    lecturers: List[str]

    # The row where the lesson appeared in the shnaton.
    # Helpful to know which lessons are considered the same (basically group + semester)
    row: int

    @cached_property
    def _split_time(self) -> Tuple[str, str]:
        """
        :return: self.time as a tuple of (start_time, end_time). If self.time == '', returns ('', '').
        """
        if not self.time:
            return '', ''

        # The format of the time field is <end_time>-<start_time>
        end_time, start_time = self.time.split('-')
        return start_time, end_time

    @property
    def start_time(self) -> str:
        return self._split_time[0]

    @property
    def end_time(self) -> str:
        return self._split_time[1]


@dataclass(frozen=True)
class Exam(HujiObject):
    date: str
    hour: str
    notes: str
    location: str
    moed: str
    semester: Semester


@dataclass(frozen=False)
class Course(HujiObject):
    faculty: str
    course_id: str
    english_name: str
    hebrew_name: str
    points: int
    semester: Semester
    language: str
    test_length: int
    test_type: str
    schedule: List[Lesson]
    exams: Optional[List[Exam]]
    hebrew_notes: str
    english_notes: str
    is_running: bool
