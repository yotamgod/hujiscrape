from .__version__ import __description__, __title__, __version__
from hujiscrape.scrapers import (
    ExamScraper,
    ShnatonCourseScraper,
    MaslulPageScraper,
    MaslulAllPageScraper,
)

from hujiscrape.magics import (
    Toar,
    ToarYear,
)

from hujiscrape.huji_objects import (
    HujiObject,
    Lesson,
    Course,
    Exam,
)

__all__ = [
    'ExamScraper',
    'ShnatonCourseScraper',
    'MaslulPageScraper',
    'MaslulAllPageScraper',
    'Toar',
    'ToarYear',
    'HujiObject',
    'Lesson',
    'Course',
    'Exam',
    '__description__',
    '__title__',
    '__version__',
    'html_to_object',
    'scrapers',
    'collectors',
    'huji_objects',
    'magics',
]
