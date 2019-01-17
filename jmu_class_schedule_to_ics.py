import requests
from icalendar import Calendar, Event
import pytz
import datetime
import hashlib
import os
import re


def sha1(data):
    return hashlib.sha1(data.encode('utf-8')).hexdigest()


def get_jmu_sid(username, password):
    password = sha1(password)
    request_data = {'flag': 1, 'unitid': 55, 'encrypt': 1, 'imgcode': '',
                    'account': username, 'appid': '273', 'password': password}
    request_result = requests.post(
        'http://oa99.jmu.edu.cn/v2/passport/api/user/login1', request_data)
    if request_result.status_code != 200:
        return -1
    else:
        return request_result.json()['sid']


def get_schedule_to_json(sid, semester):
    request_result = requests.get(
        'http://210.34.130.89/CourseSchedule/StudentCourseSchedule?sid={}&semester={}'.format(sid, semester))
    if request_result.status_code != 200:
        return -1
    else:
        return request_result.json()

def get_semesters_to_json():
    request_result = requests.get('http://labs.jmu.edu.cn/CourseSchedule/GetSemesters')
    if request_result.status_code != 200:
        return -1
    else:
        return request_result.json()

def parse_semesters_json_to_dict(semesters_json):
    semesters_dict = {}
    for item in semesters_json:
        semesters_dict[item['Code']] = item['Name']
    return semesters_dict

def get_course_take_weeks(all_week):  # 返回课程上课的周
    course_take_weeks = []
    is_interval = 0
    if '单周' in all_week:
        is_interval = 1
    elif '双周' in all_week:
        is_interval = 2
    match_object = re.match(r'(\d+)-(\d+)', all_week)
    if match_object:
        start_week = int(match_object.group(1))
        end_week = int(match_object.group(2))
        for i in range(start_week, end_week + 1):
            if is_interval == 0 or (is_interval == 1 and i % 2 != 0) or (is_interval == 2 and i % 2 == 0):
                course_take_weeks.append(i)
    return course_take_weeks


def get_course_date(first_day_date_str, course_in_day_of_week, which_week):  # 返回上课的日期
    first_day_date = datetime.datetime.strptime(
        first_day_date_str, r'%Y-%m-%d')
    return first_day_date + datetime.timedelta(days=(which_week - 1) * 7 + (course_in_day_of_week - 1))


def get_course_take_time(course_time):  # 返回上课时间
    course_time_table = {'12': [[8, 0, 0], [9, 35, 0]],
                         '34': [[10, 5, 0], [11, 40, 0]],
                         '56': [[14, 0, 0], [15, 35, 0]],
                         '78': [[15, 55, 0], [17, 30, 0]],
                         '910': [[19, 0, 0], [20, 35, 0]]}
    return course_time_table[course_time][0], course_time_table[course_time][1]


def main():
    time_zone = pytz.timezone('Asia/Shanghai')
    semesters = get_semesters_to_json()
    if semesters == -1:
        print('Program met some wrong, please wait and try again.')
        exit(1)
    print('Semesters:')
    semesters_dict = parse_semesters_json_to_dict(semesters)
    for semester in semesters:
        print(semester['Code'], '->', semester['Name'])
    selester_selected = input('Please select a semester (Just need enter the number before arrow):')
    if not semesters_dict.__contains__(selester_selected):
        print('Please select a correct semester!')
        exit(1)
    username = input('Please input your JiDaTong username:')
    password = input('Please input your JiDaTong password:')
    first_day_date_str = input('Please input first day of term(Format: Year-month-day):')
    sid = get_jmu_sid(username, password)
    if sid == -1:
        print('Your username or password is error, please try again.')
        exit(1)
    print('Your JiDaTong sid is:', sid)
    schedule_json = get_schedule_to_json(sid, selester_selected)
    if schedule_json == -1:
        print('Program met some wrong, please wait and try again.')
        exit(1)
    name = schedule_json['Name']
    class_name = schedule_json['className']
    courses = schedule_json['courses']
    calendar = Calendar()
    calendar.add('prodid', '-//My calendar product//mxm.dk//')
    calendar.add('version', '2.0')
    for course in courses:
        course_in_day_of_week = int(course['couDayTime'])  # 课程在星期几
        course_take_weeks = get_course_take_weeks(course['allWeek'])
        course_begin_time, course_end_time = get_course_take_time(course['coudeTime'])
        for week in course_take_weeks:
            course_date = get_course_date(first_day_date_str, course_in_day_of_week, week)
            event = Event()
            event.add('summary', course['couName'])
            event.add('dtstart',
                      datetime.datetime(course_date.year, course_date.month, course_date.day, course_begin_time[0],
                                        course_begin_time[1], course_begin_time[2], tzinfo=time_zone))
            event.add('dtend',
                      datetime.datetime(course_date.year, course_date.month, course_date.day, course_end_time[0],
                                        course_end_time[1], course_end_time[2], tzinfo=time_zone))
            event.add('dtstamp',
                      datetime.datetime(course_date.year, course_date.month, course_date.day, course_begin_time[0],
                                        course_begin_time[1], course_begin_time[2], tzinfo=time_zone))
            event.add('location', course['couRoom'])
            calendar.add_component(event)
    output_file_name = '{} - {}.ics'.format(class_name, name)
    output_file = open(output_file_name, 'wb')
    output_file.write(calendar.to_ical())
    output_file.close()
    print('Success write your calendar to', output_file_name)


if __name__ == '__main__':
    main()
