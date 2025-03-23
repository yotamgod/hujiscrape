import random


class FetchTask:
    def __init__(self, url: str, method: str, data: dict = None, query_params: dict = None,
                 headers: dict = None) -> None:
        self.url = url
        self.method = method
        self.data = data or {}
        self.query_params = query_params or {}
        self.headers = headers or {}


class ShnatonFetchTask(FetchTask):
    SHNATON_URL = 'https://shnaton.huji.ac.il/index.php'

    def __init__(self, data: dict = None, query_params: dict = None) -> None:
        super().__init__(url=self.SHNATON_URL, method='POST', data=data, query_params=query_params,
                         headers=self._get_default_headers())

    def _get_default_headers(self) -> dict:
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
        ]
        return {
            'user-agent': random.choice(user_agents),
        }


class ExamFetchTask(ShnatonFetchTask):
    def __init__(self, course_id: int | str, year: int):
        super().__init__(
            data={
                'peula': 'CourseD',
                'year': year,
                'detail': 'examDates',
                'course': str(course_id)
            }
        )
        self.course_id = str(course_id)
        self.year = year


class CourseFetchTask(ShnatonFetchTask):
    def __init__(self, course_id: int | str, year: int):
        super().__init__(
            data={
                'peula': 'Simple',
                'maslul': 0,
                'shana': 0,
                'year': year,
                'course': course_id
            }
        )
        self.course_id = str(course_id)
        self.year = year
