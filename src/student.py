from dataclasses import dataclass

from src.datatable import Datatable


@dataclass
class Student:
    name: str
    credit: int
    class_id: str
    course_ids: list[str]


def student_coder(student: Student) -> list[str]:
    return [student.name, str(student.credit), student.class_id, ' '.join(student.course_ids)]


def student_decoder(fields: list[str]) -> Student:
    return Student(fields[0], int(fields[1]), fields[2], fields[3].split(' ') if fields[3] else [])

student_table = Datatable('student', student_decoder, student_coder)


@dataclass
class Class:
    name: str
    credit_limit: int

def class_coder(class_: Class) -> list[str]:
    return [class_.name, str(class_.credit_limit)]

def class_decoder(fields: list[str]) -> Class:
    return Class(fields[0], int(fields[1]))

class_table = Datatable('class', class_decoder, class_coder)

@dataclass
class Course:
    name: str
    teacher: str
    sections: list[str]
    credit: int
    required: bool

def course_coder(course: Course) -> list[str]:
    return [course.name, course.teacher, ' '.join(course.sections), str(course.credit), '1' if course.required else '0']

def course_decoder(fields: list[str]) -> Course:
    return Course(fields[0], fields[1], fields[2].split(' ') if fields[2] else [], int(fields[3]), fields[4] == '1')

course_table = Datatable('course', course_decoder, course_coder)

