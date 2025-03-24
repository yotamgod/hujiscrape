from dataclasses import dataclass
from functools import cached_property
from typing import List, Optional, Tuple


class HujiObject:
    pass


@dataclass(frozen=True)
class Lesson(HujiObject):
    location: str
    passing_type: str  # Meaning in campus / videotaped etc...
    time: str
    day: str
    semester: str
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
        try:
            # The format of the time field is <end_time>-<start_time>
            end_time, start_time = self.time.split('-')
        except ValueError:
            return '', ''

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
    semester: str


@dataclass(frozen=False)
class Course(HujiObject):
    course_id: str
    hebrew_name: str
    english_name: str
    department: str
    faculty: str
    semester: str
    weekly_hours: int
    credits: int
    language: str
    exam_length: float
    exam_type: str  # Project, written test, ...
    schedule: List[Lesson]
    exams: Optional[List[Exam]]
    hebrew_notes: str
    english_notes: str
    is_running: bool
    syllabus_url: str
    moodle_url: str
