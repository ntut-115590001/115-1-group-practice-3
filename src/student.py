from dataclasses import dataclass
from typing import Self

from src.datatable import Datatable, Datarow
from src.util import bool_to_str, join_map, split_map


@dataclass
class Class_(Datarow):
    name: str
    credit_limit: int

    @classmethod
    def unserialize(cls, fields: list[str]) -> Self:
        return cls(fields[0], int(fields[1]))

    def serialize(self) -> list[str]:
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
    def unserialize(cls, fields: list[str]) -> Self:
        return cls(fields[0], fields[1], split_map(fields[2]), int(fields[3]), bool(fields[4]))

    def serialize(self) -> list[str]:
        return [self.name, self.teacher, join_map(self.sections), str(self.credit), bool_to_str(self.required)]

course_table = Datatable('course', Course)


@dataclass
class Student(Datarow):
    name: str
    credit: int
    class_id: str
    course_ids: list[str]

    @classmethod
    def unserialize(cls, fields: list[str]) -> Self:
        return cls(fields[0], int(fields[1]), fields[2], split_map(fields[3]))

    def serialize(self) -> list[str]:
        return [self.name, str(self.credit), self.class_id, join_map(self.course_ids)]

    @property
    def class_(self) -> Class_ | None:
        return class_table.get(self.class_id)

student_table = Datatable('student', Student)

