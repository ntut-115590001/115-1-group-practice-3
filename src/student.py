from dataclasses import dataclass
from typing import Self

from src.datatable import Datatable, Datarow


@dataclass
class Class_(Datarow):
    name: str
    credit_limit: int

    @classmethod
    def serialize(cls, fields: list[str]) -> Self:
        return cls(fields[0], int(fields[1]))

    def unserialize(self) -> list[str]:
        return [self.name, str(self.credit_limit)]

class_table = Datatable('class', Class_)

@dataclass
class Course(Datarow):
    name: str
    teacher: str
    sections: list[str]
    credit: int
    required: bool

    @classmethod
    def serialize(cls, fields: list[str]) -> Self:
        return cls(fields[0], fields[1], fields[2].split(' ') if fields[2] else [], int(fields[3]), fields[4] == '1')

    def unserialize(self) -> list[str]:
        return [self.name, self.teacher, ' '.join(self.sections), str(self.credit), '1' if self.required else '0']

course_table = Datatable('course', Course)

@dataclass
class Student(Datarow):
    name: str
    credit: int
    class_id: str
    course_ids: list[str]

    @classmethod
    def serialize(cls, fields: list[str]) -> Self:
        return cls(fields[0], int(fields[1]), fields[2], fields[3].split(' ') if fields[3] else [])

    def unserialize(self) -> list[str]:
        return [self.name, str(self.credit), self.class_id, ' '.join(self.course_ids)]

    @property
    def class_(self) -> Class_ | None:
        return class_table.get(self.class_id)


student_table = Datatable('student', Student)
