"""F1: course and student data management."""

from dataclasses import dataclass
from typing import Self

from src.cli import CommandError, command
from src.datatable import Datatable
from src.util import join_map, split_map


def parse_section(text: str) -> tuple[list[str], str]:
    """'13,14@R101' -> (['13', '14'], 'R101')"""
    times, room = text.split('@')
    return (split_map(times, sep=','), room)


def section_to_text(section: tuple[list[str], str]) -> str:
    """(['13', '14'], 'R101') -> '13,14@R101'"""
    times, room = section
    return join_map(times, sep=',') + '@' + room


@dataclass
class Course:
    name: str
    credit: int
    teachers: list[str]
    sections: list[tuple[list[str], str]]
    student_limit: int

    @classmethod
    def unserialize(cls, fields: list[str]) -> Self:
        name, credit, teachers, sections, limit = fields
        return cls(
            name,
            int(credit),
            split_map(teachers),
            split_map(sections, parse_section, sep=';'),
            int(limit),
        )

    def serialize(self) -> list[str]:
        return [
            self.name,
            str(self.credit),
            join_map(self.teachers),
            join_map(self.sections, section_to_text, sep=';'),
            str(self.student_limit),
        ]


courses = Datatable('courses', Course)
DAYS = '1234567'
PERIODS = '123456789abc'


def check_time(time: str) -> bool:
    return len(time) == 2 and time[0] in DAYS and time[1] in PERIODS


@command('course_add')
def course_add(code: str, name: str, credit: str, teachers: str,
               sections: str, limit: str) -> None:
    """新增課程。語法：course_add <課號> <課名> <學分> <教師> <時段> <人數上限>

    教師以逗號分隔；時段格式如 13,14@R101;2a@R205。
    """
    if code in courses:
        raise CommandError(f'課號 {code} 已存在！')

    try:
        credit_n = int(credit)
        limit_n = int(limit)
    except ValueError as err:
        raise CommandError('學分與人數上限必須是整數！') from err
    if credit_n <= 0:
        raise CommandError('學分必須是正整數！')
    if limit_n < 1:
        raise CommandError('人數上限不得小於 1！')

    try:
        section_list = split_map(sections, parse_section, sep=';')
    except ValueError as err:
        raise CommandError('時段格式錯誤，應為 13,14@R101;2a@R205') from err
    if not section_list:
        raise CommandError('至少需要一個時段！')
    for times, room in section_list:
        if not times or not room:
            raise CommandError('每個時段都需要節次與教室！')
        for t in times:
            if not check_time(t):
                raise CommandError(f'無效的時段：{t}')

    courses[code] = Course(name, credit_n, split_map(teachers, sep=','),
                           section_list, limit_n)
    print(f'已新增課程 {code}。')


DAY_NAMES = {'1': 'Mon', '2': 'Tue', '3': 'Wed', '4': 'Thu',
             '5': 'Fri', '6': 'Sat', '7': 'Sun'}


def format_time(time: str) -> str:
    """'13' -> 'Mon 3'"""
    return f'{DAY_NAMES[time[0]]} {time[1]}'


def print_course(code: str, course: Course) -> None:
    print(f'Course: {code}')
    print(f'Name: {course.name}')
    print(f'Credits: {course.credit}')
    print(f'Instructor: {", ".join(course.teachers)}')
    count = enrolled_count(code)
    print(f'Enrolled: {count} / {course.student_limit}')
    print(f'Remaining seats: {course.student_limit - count}')
    for times, room in course.sections:
        print(f'Time: {", ".join(format_time(t) for t in times)}')
        print(f'Classroom: {room}')
    print()


@command('course_query')
def course_query(field: str | None = None, value: str | None = None) -> None:
    """查詢課程。語法：course_query [(code|teacher|day|seats|required|elective) <值>]

    不帶參數時列出所有課程。
    code <課號>：依課號查詢。
    teacher <教師>：依授課教師查詢。
    day <1-7>：依星期查詢。
    seats <N>：剩餘名額不少於 N 的課程。
    required <系級代號>：該系級的必修課。
    elective <系級代號>：該系級的選修課。
    """
    if field is None:
        found = list(courses.items())
    elif value is None:
        raise CommandError('請提供查詢值！')
    elif field == 'code':
        found = [(value, courses[value])] if value in courses else []
    elif field == 'teacher':
        found = [(c, x) for c, x in courses.items() if value in x.teachers]
    elif field == 'day':
        found = [(c, x) for c, x in courses.items()
                 if any(t[0] == value for times, _ in x.sections for t in times)]
    elif field in ('required', 'elective'):
        if value not in classes:
            raise CommandError(f'系級 {value} 不存在！')
        required = classes[value].required_course_ids
        if field == 'required':
            found = [(c, x) for c, x in courses.items() if c in required]
        else:
            found = [(c, x) for c, x in courses.items() if c not in required]
    elif field == 'seats':
        try:
            need = int(value)
        except ValueError as err:
            raise CommandError('名額必須是整數！') from err
        found = [(c, x) for c, x in courses.items()
                 if x.student_limit - enrolled_count(c) >= need]
    else:
        raise CommandError(f'未知查詢欄位：{field}')

    if not found:
        print('Not found')
        return
    print(f'Found {len(found)} course(s).')
    print()
    for code, course in found:
        print_course(code, course)


@dataclass
class Student:
    name: str
    class_ids: list[str]
    course_ids: list[str]

    @classmethod
    def unserialize(cls, fields: list[str]) -> Self:
        name, class_ids, course_ids = fields
        return cls(name, split_map(class_ids), split_map(course_ids))

    def serialize(self) -> list[str]:
        return [self.name, join_map(self.class_ids), join_map(self.course_ids)]


@dataclass
class ClassGroup:
    name: str
    credit_limit: int
    required_course_ids: list[str]

    @classmethod
    def unserialize(cls, fields: list[str]) -> Self:
        name, credit_limit, required = fields
        return cls(name, int(credit_limit), split_map(required))

    def serialize(self) -> list[str]:
        return [self.name, str(self.credit_limit), join_map(self.required_course_ids)]


students = Datatable('student', Student)
classes = Datatable('class', ClassGroup)


def enrolled_count(course_code: str) -> int:
    return sum(course_code in s.course_ids for s in students.values())


@command('student_add')
def student_add(student_id: str, name: str, class_ids: str,
                course_ids: str = '') -> None:
    """新增學生。語法：student_add <學號> <姓名> <系級> [<已選課程>]

    系級與已選課程以逗號分隔。
    """
    if student_id in students:
        raise CommandError(f'學號 {student_id} 已存在！')
    class_list = split_map(class_ids, sep=',')
    for cid in class_list:
        if cid not in classes:
            raise CommandError(f'系級 {cid} 不存在！')
    course_list = split_map(course_ids, sep=',')
    for c in course_list:
        if c not in courses:
            raise CommandError(f'課程 {c} 不存在！')
        if enrolled_count(c) >= courses[c].student_limit:
            raise CommandError(f'課程 {c} 已額滿！')
    students[student_id] = Student(name, class_list, course_list)
    print(f'已新增學生 {student_id}。')


@command('course_delete')
def course_delete(code: str) -> None:
    """刪除課程。語法：course_delete <課號>

    已有學生選修的課程不能刪除。
    """
    if code not in courses:
        raise CommandError(f'課號 {code} 不存在！')
    count = enrolled_count(code)
    if count > 0:
        raise CommandError(f'課程 {code} 已有 {count} 位學生選修，不能刪除！')
    del courses[code]
    print(f'已刪除課程 {code}。')


def parse_credit(text: str) -> int:
    try:
        value = int(text)
    except ValueError as err:
        raise CommandError('學分必須是整數！') from err
    if value <= 0:
        raise CommandError('學分必須是正整數！')
    return value


def parse_limit(text: str) -> int:
    try:
        value = int(text)
    except ValueError as err:
        raise CommandError('人數上限必須是整數！') from err
    if value < 1:
        raise CommandError('人數上限不得小於 1！')
    return value


def parse_sections(text: str) -> list[tuple[list[str], str]]:
    try:
        result = split_map(text, parse_section, sep=';')
    except ValueError as err:
        raise CommandError('時段格式錯誤，應為 13,14@R101;2a@R205') from err
    if not result:
        raise CommandError('至少需要一個時段！')
    for times, room in result:
        if not times or not room:
            raise CommandError('每個時段都需要節次與教室！')
        for t in times:
            if not check_time(t):
                raise CommandError(f'無效的時段：{t}')
    return result


@command('course_modify')
def course_modify(code: str, field: str, value: str) -> None:
    """修改課程。語法：course_modify <課號> <欄位> <新值>

    欄位：name、credit、teachers、sections、limit。
    """
    if code not in courses:
        raise CommandError(f'課號 {code} 不存在！')
    course = courses[code]
    if field == 'name':
        course.name = value
    elif field == 'credit':
        course.credit = parse_credit(value)
    elif field == 'teachers':
        course.teachers = split_map(value, sep=',')
    elif field == 'sections':
        course.sections = parse_sections(value)
    elif field == 'limit':
        new_limit = parse_limit(value)
        count = enrolled_count(code)
        if new_limit < count:
            raise CommandError(f'人數上限不得小於目前已選人數 {count}！')
        course.student_limit = new_limit
    else:
        raise CommandError(f'未知欄位：{field}')
    print(f'已修改課程 {code}。')


@command('student_query')
def student_query(student_id: str | None = None) -> None:
    """查詢學生。語法：student_query [<學號>]

    不帶參數時列出所有學生。
    """
    if student_id is None:
        found = list(students.items())
    elif student_id in students:
        found = [(student_id, students[student_id])]
    else:
        found = []
    if not found:
        print('Not found')
        return
    print(f'Found {len(found)} student(s).')
    print()
    for sid, s in found:
        print(f'Student: {sid}')
        print(f'Name: {s.name}')
        print(f'Class: {", ".join(s.class_ids)}')
        print(f'Courses: {", ".join(s.course_ids)}')
        print()


@command('student_delete')
def student_delete(student_id: str) -> None:
    """刪除學生。語法：student_delete <學號>

    學生的選課紀錄隨之刪除，其名額自動釋放。
    """
    if student_id not in students:
        raise CommandError(f'學號 {student_id} 不存在！')
    del students[student_id]
    print(f'已刪除學生 {student_id}。')


@command('class_add')
def class_add(class_id: str, name: str, credit_limit: str,
              required: str = '') -> None:
    """新增系級。語法：class_add <系級代號> <名稱> <學分上限> [<必修課程>]

    必修課程以逗號分隔。
    """
    if class_id in classes:
        raise CommandError(f'系級 {class_id} 已存在！')
    limit = parse_credit(credit_limit)
    required_list = split_map(required, sep=',')
    for c in required_list:
        if c not in courses:
            raise CommandError(f'課程 {c} 不存在！')
    classes[class_id] = ClassGroup(name, limit, required_list)
    print(f'已新增系級 {class_id}。')


@command('class_query')
def class_query(class_id: str | None = None) -> None:
    """查詢系級。語法：class_query [<系級代號>]

    不帶參數時列出所有系級。
    """
    if class_id is None:
        found = list(classes.items())
    elif class_id in classes:
        found = [(class_id, classes[class_id])]
    else:
        found = []
    if not found:
        print('Not found')
        return
    print(f'Found {len(found)} class(es).')
    print()
    for cid, c in found:
        print(f'Class: {cid}')
        print(f'Name: {c.name}')
        print(f'Credit limit: {c.credit_limit}')
        print(f'Required courses: {", ".join(c.required_course_ids)}')
        print()


@command('student_modify')
def student_modify(student_id: str, field: str, value: str) -> None:
    """修改學生。語法：student_modify <學號> <欄位> <新值>

    欄位：name、class、courses（後兩者以逗號分隔）。
    """
    if student_id not in students:
        raise CommandError(f'學號 {student_id} 不存在！')
    student = students[student_id]
    if field == 'name':
        student.name = value
    elif field == 'class':
        class_list = split_map(value, sep=',')
        for cid in class_list:
            if cid not in classes:
                raise CommandError(f'系級 {cid} 不存在！')
        student.class_ids = class_list
    elif field == 'courses':
        course_list = split_map(value, sep=',')
        for c in course_list:
            if c not in courses:
                raise CommandError(f'課程 {c} 不存在！')
            if (c not in student.course_ids and
                    enrolled_count(c) >= courses[c].student_limit):
                raise CommandError(f'課程 {c} 已額滿！')
        student.course_ids = course_list
    else:
        raise CommandError(f'未知欄位：{field}')
    print(f'已修改學生 {student_id}。')


@command('class_modify')
def class_modify(class_id: str, field: str, value: str) -> None:
    """修改系級。語法：class_modify <系級代號> <欄位> <新值>

    欄位：name、credit_limit、required（必修課程以逗號分隔）。
    """
    if class_id not in classes:
        raise CommandError(f'系級 {class_id} 不存在！')
    group = classes[class_id]
    if field == 'name':
        group.name = value
    elif field == 'credit_limit':
        group.credit_limit = parse_credit(value)
    elif field == 'required':
        required_list = split_map(value, sep=',')
        for c in required_list:
            if c not in courses:
                raise CommandError(f'課程 {c} 不存在！')
        group.required_course_ids = required_list
    else:
        raise CommandError(f'未知欄位：{field}')
    print(f'已修改系級 {class_id}。')


@command('class_delete')
def class_delete(class_id: str) -> None:
    """刪除系級。語法：class_delete <系級代號>

    仍有學生隸屬的系級不能刪除。
    """
    if class_id not in classes:
        raise CommandError(f'系級 {class_id} 不存在！')
    members = [sid for sid, s in students.items() if class_id in s.class_ids]
    if members:
        raise CommandError(f'系級 {class_id} 仍有 {len(members)} 位學生，不能刪除！')
    del classes[class_id]
    print(f'已刪除系級 {class_id}。')
