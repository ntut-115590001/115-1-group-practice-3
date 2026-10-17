import unittest
from io import StringIO
from unittest.mock import patch

from src import f1
from src.cli import CommandError


class TestF1(unittest.TestCase):
    def setUp(self):
        f1.courses.clear()
        f1.students.clear()
        f1.classes.clear()
        patcher = patch('sys.stdout', new_callable=StringIO)
        self.stdout = patcher.start()
        self.addCleanup(patcher.stop)

    def output(self) -> str:
        return self.stdout.getvalue()

    def clear_output(self):
        self.stdout.truncate(0)
        self.stdout.seek(0)

    def add_course(self, code: str = 'CS101', limit: str = '40'):
        f1.course_add(code, 'Intro', '3', 'Lin', '13,14@R101', limit)

    def add_class(self, class_id: str = 'CS1', required: str = ''):
        f1.class_add(class_id, 'CS Year 1', '25', required)

    # Normal cases

    def test_add_course(self):
        f1.course_add('CS101', 'Intro', '3', 'Lin,Wang', '13,14@R101;2a@R205', '40')
        course = f1.courses['CS101']
        self.assertEqual(course.name, 'Intro')
        self.assertEqual(course.credit, 3)
        self.assertEqual(course.teachers, ['Lin', 'Wang'])
        self.assertEqual(course.sections, [(['13', '14'], 'R101'), (['2a'], 'R205')])
        self.assertEqual(course.student_limit, 40)

    def test_serialize_roundtrip(self):
        f1.course_add('CS101', 'Intro', '3', 'Lin,Wang', '13,14@R101;2a@R205', '40')
        course = f1.courses['CS101']
        self.assertEqual(f1.Course.unserialize(course.serialize()), course)
        self.add_class('CS1', 'CS101')
        f1.student_add('S001', 'Ana', 'CS1', 'CS101')
        student = f1.students['S001']
        self.assertEqual(f1.Student.unserialize(student.serialize()), student)
        group = f1.classes['CS1']
        self.assertEqual(f1.ClassGroup.unserialize(group.serialize()), group)

    def test_query_filters(self):
        self.add_course('CS101')
        f1.course_add('MA101', 'Calculus', '4', 'Wang', '21@R205', '50')
        for args, present, absent in (
            (('code', 'CS101'), 'Course: CS101', 'Course: MA101'),
            (('teacher', 'Wang'), 'Course: MA101', 'Course: CS101'),
            (('day', '1'), 'Course: CS101', 'Course: MA101'),
            (('day', '2'), 'Course: MA101', 'Course: CS101'),
        ):
            with self.subTest(args=args):
                self.clear_output()
                f1.course_query(*args)
                self.assertIn(present, self.output())
                self.assertNotIn(absent, self.output())
        self.clear_output()
        f1.course_query()
        self.assertIn('Found 2 course(s).', self.output())
        self.clear_output()
        f1.course_query('teacher', 'Nobody')
        self.assertIn('Not found', self.output())

    def test_remaining_seats(self):
        self.add_course()
        self.add_class()
        f1.student_add('S001', 'Ana', 'CS1', 'CS101')
        self.clear_output()
        f1.course_query('code', 'CS101')
        self.assertIn('Enrolled: 1 / 40', self.output())
        self.assertIn('Remaining seats: 39', self.output())

    def test_modify_course(self):
        self.add_course()
        f1.course_modify('CS101', 'name', 'New')
        f1.course_modify('CS101', 'credit', '2')
        f1.course_modify('CS101', 'teachers', 'A,B')
        f1.course_modify('CS101', 'sections', '3b@R300')
        f1.course_modify('CS101', 'limit', '10')
        course = f1.courses['CS101']
        self.assertEqual(course.name, 'New')
        self.assertEqual(course.credit, 2)
        self.assertEqual(course.teachers, ['A', 'B'])
        self.assertEqual(course.sections, [(['3b'], 'R300')])
        self.assertEqual(course.student_limit, 10)

    def test_delete_course(self):
        self.add_course()
        f1.course_delete('CS101')
        self.assertNotIn('CS101', f1.courses)

    def test_delete_student_frees_seats(self):
        self.add_course()
        self.add_class()
        f1.student_add('S001', 'Ana', 'CS1', 'CS101')
        self.assertEqual(f1.enrolled_count('CS101'), 1)
        f1.student_delete('S001')
        self.assertEqual(f1.enrolled_count('CS101'), 0)
        f1.course_delete('CS101')  # now allowed
        self.assertNotIn('CS101', f1.courses)

    def test_modify_student(self):
        self.add_course()
        f1.course_add('MA101', 'Calculus', '4', 'Wang', '21@R205', '50')
        self.add_class('CS1')
        self.add_class('EE1')
        f1.student_add('S001', 'Ana', 'CS1')
        f1.student_modify('S001', 'name', 'Anna')
        f1.student_modify('S001', 'class', 'CS1,EE1')
        f1.student_modify('S001', 'courses', 'CS101,MA101')
        student = f1.students['S001']
        self.assertEqual(student.name, 'Anna')
        self.assertEqual(student.class_ids, ['CS1', 'EE1'])
        self.assertEqual(student.course_ids, ['CS101', 'MA101'])

    def test_required_and_elective_query(self):
        self.add_course('CS101')
        f1.course_add('MA101', 'Calculus', '4', 'Wang', '21@R205', '50')
        self.add_class('CS1', 'CS101')
        self.clear_output()
        f1.course_query('required', 'CS1')
        self.assertIn('Course: CS101', self.output())
        self.assertNotIn('Course: MA101', self.output())
        self.clear_output()
        f1.course_query('elective', 'CS1')
        self.assertIn('Course: MA101', self.output())
        self.assertNotIn('Course: CS101', self.output())

    def test_class_and_student_query(self):
        self.add_course()
        self.add_class('CS1', 'CS101')
        f1.student_add('S001', 'Ana', 'CS1', 'CS101')
        self.clear_output()
        f1.class_query('CS1')
        self.assertIn('Required courses: CS101', self.output())
        self.clear_output()
        f1.student_query('S001')
        self.assertIn('Name: Ana', self.output())
        self.clear_output()
        f1.student_query('NOPE')
        self.assertIn('Not found', self.output())

    #Boundary cases

    def test_minimum_values(self):
        f1.course_add('A', 'x', '1', 'T', '11@R1', '1')
        self.assertEqual(f1.courses['A'].credit, 1)
        self.assertEqual(f1.courses['A'].student_limit, 1)

    def test_time_boundaries(self):
        for t in ('11', '1c', '71', '7c', '19', '7a'):
            with self.subTest(time=t):
                self.assertTrue(f1.check_time(t))
        for t in ('', '1', '7', '01', '81', '1d', '111', '1C'):
            with self.subTest(time=t):
                self.assertFalse(f1.check_time(t))

    def test_limit_equal_to_enrolled(self):
        self.add_course('CS101', '2')
        self.add_class()
        f1.student_add('S001', 'Ana', 'CS1', 'CS101')
        f1.student_add('S002', 'Beto', 'CS1', 'CS101')
        f1.course_modify('CS101', 'limit', '2')  # equal to enrolled: allowed
        self.assertRaises(CommandError, f1.course_modify, 'CS101', 'limit', '1')

    def test_course_full_in_modify(self):
        self.add_course('CS101', '1')
        self.add_class()
        f1.student_add('S001', 'Ana', 'CS1', 'CS101')
        f1.student_add('S002', 'Beto', 'CS1')
        self.assertRaises(CommandError, f1.student_modify, 'S002', 'courses', 'CS101')

    def test_seats_query_boundary(self):
        self.add_course('CS101', '40')
        self.clear_output()
        f1.course_query('seats', '40')
        self.assertIn('Course: CS101', self.output())
        self.clear_output()
        f1.course_query('seats', '41')
        self.assertIn('Not found', self.output())

    #Error cases

    def test_add_course_errors(self):
        self.add_course()
        for args in (
            ('CS101', 'x', '3', 'T', '13@R1', '10'),   # duplicate code
            ('C2', 'x', '0', 'T', '13@R1', '10'),      # credit 0
            ('C2', 'x', '-1', 'T', '13@R1', '10'),     # negative credit
            ('C2', 'x', 'abc', 'T', '13@R1', '10'),    # credit not a number
            ('C2', 'x', '3', 'T', '13@R1', '0'),       # limit 0
            ('C2', 'x', '3', 'T', '13@R1', 'abc'),     # limit not a number
            ('C2', 'x', '3', 'T', '93@R1', '10'),      # invalid day
            ('C2', 'x', '3', 'T', '1d@R1', '10'),      # invalid period
            ('C2', 'x', '3', 'T', '13', '10'),         # no classroom separator
            ('C2', 'x', '3', 'T', '@R1', '10'),        # no time
            ('C2', 'x', '3', 'T', '13@', '10'),        # no classroom
            ('C2', 'x', '3', 'T', '', '10'),           # no section
        ):
            with self.subTest(args=args):
                self.assertRaises(CommandError, f1.course_add, *args)
                self.assertNotIn('C2', f1.courses)

    def test_delete_course_errors(self):
        self.assertRaises(CommandError, f1.course_delete, 'NOPE')
        self.add_course()
        self.add_class()
        f1.student_add('S001', 'Ana', 'CS1', 'CS101')
        self.assertRaises(CommandError, f1.course_delete, 'CS101')
        self.assertIn('CS101', f1.courses)

    def test_modify_course_errors(self):
        self.add_course()
        for args in (
            ('NOPE', 'name', 'x'),
            ('CS101', 'credit', '0'),
            ('CS101', 'credit', 'x'),
            ('CS101', 'limit', '0'),
            ('CS101', 'sections', '93@R1'),
            ('CS101', 'color', 'red'),
        ):
            with self.subTest(args=args):
                self.assertRaises(CommandError, f1.course_modify, *args)

    def test_student_errors(self):
        self.add_course()
        self.add_class()
        f1.student_add('S001', 'Ana', 'CS1', 'CS101')
        for args in (
            ('S001', 'Dup', 'CS1'),
            ('S002', 'X', 'ZZ9'),
            ('S002', 'X', 'CS1', 'NOPE'),
        ):
            with self.subTest(args=args):
                self.assertRaises(CommandError, f1.student_add, *args)
        self.assertRaises(CommandError, f1.student_delete, 'NOPE')
        for args in (
            ('NOPE', 'name', 'x'),
            ('S001', 'class', 'ZZ9'),
            ('S001', 'courses', 'NOPE'),
            ('S001', 'age', '20'),
        ):
            with self.subTest(args=args):
                self.assertRaises(CommandError, f1.student_modify, *args)

    def test_student_add_to_full_course(self):
        self.add_course('CS101', '1')
        self.add_class()
        f1.student_add('S001', 'Ana', 'CS1', 'CS101')
        self.assertRaises(CommandError, f1.student_add, 'S002', 'Beto', 'CS1', 'CS101')
        self.assertNotIn('S002', f1.students)

    def test_class_errors(self):
        self.add_class()
        for args in (
            ('CS1', 'x', '25'),           # duplicate id
            ('C2', 'x', '0'),             # credit limit 0
            ('C2', 'x', 'abc'),           # not a number
            ('C2', 'x', '25', 'NOPE'),    # unknown required course
        ):
            with self.subTest(args=args):
                self.assertRaises(CommandError, f1.class_add, *args)

    def test_query_errors(self):
        self.add_course()
        for args in (
            ('color', 'red'),
            ('code',),
            ('seats', 'abc'),
            ('required', 'NOPE'),
        ):
            with self.subTest(args=args):
                self.assertRaises(CommandError, f1.course_query, *args)


if __name__ == '__main__':
    unittest.main()  #no cover