import asyncio

from bs4 import BeautifulSoup
import re
import json

from raw_suppliers import RequestCourseSupplier

# def extract_course_info(course_element):
#     title_element = course_element.select_one('.courseTitle')
#     english_title_element = title_element.find_next('b')
#     hebrew_title_element = english_title_element.find_next('b')
#     course_code_element = hebrew_title_element.find_next('b')
#     english_title = english_title_element.text.strip()
#     hebrew_title = hebrew_title_element.text.strip()
#     course_code = re.search(r'\d+', course_code_element.text).group()
#
#     # duration = course_element.select_one('.courseTD:nth-child(1)').text.strip()
#     # exam_type = course_element.select_one('.courseTD:nth-child(2)').text.strip()
#     # credits = course_element.select_one('.courseTD:nth-child(3)').text.strip()
#     # points = course_element.select_one('.courseTD:nth-child(4)').text.strip()
#     # semester = course_element.select_one('.courseTD:nth-child(5)').text.strip()
#     # lecturer = course_element.select_one('.courseTD:nth-child(8)').text.strip()
#
#     schedule_rows = course_element.find_all('#details{} tr'.format(course_code))
#     schedule = []
#     for row in schedule_rows[1:]:  # Skip the header row
#         columns = row.select('td.courseDet.text')
#         location = columns[0].text.strip()
#         lesson_type = columns[6].text.strip()
#         time = columns[2].text.strip()
#         day = columns[3].text.strip()
#         group = columns[5].text.strip()
#         schedule.append({
#             'location': location,
#             'type': lesson_type,
#             'time': time,
#             'day': day,
#             # 'semester': semester,
#             'group': group,
#             'lessonType': 'שעור' if lesson_type == 'שעור' else 'תרג',  # Assuming "שעור" or "תרג" in the lesson type
#             # 'lecturer': lecturer
#         })
#
#     note = course_element.select_one('.courseDet.text[style="padding-right:10px;text-align:right"]').text.strip()
#
#     return {
#         'courseTitle': english_title,
#         'courseEnglishTitle': english_title,
#         'courseHebrewTitle': hebrew_title,
#         'courseCode': course_code,
#         # 'duration': duration,
#         # 'examType': exam_type,
#         'credits': credits,
#         # 'points': points,
#         # 'semester': semester,
#         # 'lecturer': lecturer,
#         'schedule': schedule,
#         'note': note,
#     }
#
# def convert_html_to_json(html_data):
#     soup = BeautifulSoup(html_data, 'html.parser')
#     courses = soup.find_all('div', class_='courseTitle')
#     course_info_list = [extract_course_info(course.parent) for course in courses]
#     return json.dumps(course_info_list, ensure_ascii=False, indent=2)


# # Call the function to get the JSON string
# json_data = convert_html_to_json(html_data)
# print(json_data)

async def test():
    s = RequestCourseSupplier("67504", 2024)
    return await s.supply()

if __name__ == '__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test())
