from .__version__ import __description__, __title__, __version__
from hujiscrape.scrapers import (
    ExamScraper,
    ShnatonByCourseIdScraper,
)

from hujiscrape.magics import (
    Toar,
    ToarYear,
    Semester
)

from hujiscrape.huji_objects import (
    HujiObject,
    Lesson,
    Course,
    Exam,
)

__all__ = [
    'ExamScraper',
    'ShnatonByCourseIdScraper',
    'Toar',
    'ToarYear',
    'Semester',
    'HujiObject',
    'Lesson',
    'Course',
    'Exam',
    '__description__',
    '__title__',
    '__version__',
    'html_to_object',
    'scrapers',
    'fetchers',
    'fetch_tasks',
    'huji_objects',
    'magics',
]
