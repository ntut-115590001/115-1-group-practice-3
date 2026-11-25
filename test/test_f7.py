"""F7 acceptance tests through the same command dispatcher used by start.py."""

import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from src import cli
from src.data_management import Course, Student, courses, students


class SearchTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.dict(courses, clear=True))
        self.enterContext(patch.dict(students, clear=True))
        self.course('R', 2, '12')
        self.course('A', 2, '13')
        self.course('B', 2, '22')

    def course(self, code, credits, *slots):
        courses[code] = Course(code, credits, ['Lin'],
                               [([slot], 'R101') for slot in slots], 1)

    def run_search(self, arguments, expected=cli.Result.SUCCESS):
        output = StringIO()
        with redirect_stdout(output):
            result = cli.run('schedule_search ' + arguments)
        self.assertEqual(result, expected, output.getvalue())
        return output.getvalue().strip().splitlines()

    def test_commute_weight_reverses_the_winner(self):
        args = 'R A,B 4 4 - B'
        self.assertEqual(self.run_search(args), [
            'A,R | 4 學分 | -10.00 分', 'B,R | 4 學分 | -14.00 分'])
        self.assertEqual(self.run_search(args + ' 2-6 2,3,5,2,6'), [
            'B,R | 4 學分 | 2.00 分', 'A,R | 4 學分 | -2.00 分'])

    def test_all_subsets_credit_endpoints_ties_and_duplicate_ids(self):
        self.assertEqual(self.run_search('R,R R,B,A,A 2 6 - - 2-6 0,0,0,0,0'), [
            'A,B,R | 6 學分 | 0.00 分', 'A,R | 4 學分 | 0.00 分',
            'B,R | 4 學分 | 0.00 分', 'R | 2 學分 | 0.00 分'])

    def test_optional_conflicts_second_meeting_blocked_or_full(self):
        self.course('C', 2, '32', '12')
        self.course('D', 2, '32', '7c')
        students['S'] = Student('Student', [], ['B'])
        self.assertEqual(self.run_search('R A,B,C,D 4 4 7c'), [
            'A,R | 4 學分 | -10.00 分'])
        self.assertEqual(students['S'].course_ids, ['B'])

    def test_conflicts_between_two_electives(self):
        self.course('C', 2, '13')
        self.assertEqual(self.run_search('R A,C 6 6'), ['無可行課表'])

    def test_impossible_required_or_credit_bounds(self):
        self.course('C', 2, '12')
        students['S'] = Student('Student', [], ['B'])
        for args in ('R,C A 0 6', 'B A 0 6', 'R A 0 6 12',
                     'R A 0 1', 'R A 5 6'):
            with self.subTest(args=args):
                self.assertEqual(self.run_search(args), ['無可行課表'])

    def test_empty_schedule_and_no_candidates(self):
        self.assertEqual(self.run_search('- - 0 0'), ['（空課表） | 0 學分 | 0.00 分'])
        self.assertEqual(self.run_search('- - 1 2'), ['無可行課表'])

    def test_individual_metrics_multiple_days_and_letter_periods(self):
        self.course('X', 2, '11', '13', '19', '1a', '7c')
        self.course('Y', 2, '1b')
        # Two days, six internal gaps, one early day, three slots outside 9-b.
        # 11 and 13 are before the window, 7c is after it. One of two electives is preferred.
        for weights, score in [('1,0,0,0,0', '-2.00'), ('0,1,0,0,0', '-6.00'),
                               ('0,0,1,0,0', '-1.00'), ('0,0,0,1,0', '-3.00'),
                               ('0,0,0,0,1', '0.50')]:
            with self.subTest(weights=weights):
                self.assertEqual(self.run_search('- X,Y 4 4 - X 9-b ' + weights),
                                 [f'X,Y | 4 學分 | {score} 分'])

    def test_invalid_arguments(self):
        for args in ('R A x 4', 'R A 4 2', 'R A -1 4', 'Z A 0 4',
                     'R Z 0 4', 'R A 0 4 1d', 'R A 0 4 - Z',
                     'R A 0 4 - - 6-2', 'R A 0 4 - - 0-3',
                     'R A 0 4 - - 1-22', 'R A 0 4 - - 2-6 1,2',
                     'R A 0 4 - - 2-6 1,2,3,-1,5', 'R A 0 4 - - 2-6 a,b,c,d,e'):
            with self.subTest(args=args):
                self.run_search(args, cli.Result.FAIL)
