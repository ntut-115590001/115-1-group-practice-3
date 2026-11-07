import unittest
from io import StringIO
from unittest.mock import patch

from src import data_management as dm
from src import schedule as sc
from src.cli import CommandError


class TestSchedule(unittest.TestCase):
    def setUp(self):
        dm.courses.clear()
        dm.students.clear()
        dm.classes.clear()
        patcher = patch('sys.stdout', new_callable=StringIO)
        self.stdout = patcher.start()
        self.addCleanup(patcher.stop)
        dm.class_add('CS1', 'CS Year 1', '25', '')
        self.clear_output()

    def output(self) -> str:
        return self.stdout.getvalue()

    def clear_output(self):
        self.stdout.truncate(0)
        self.stdout.seek(0)

    def add_course(self, code: str, sections: str, credit: str = '3'):
        dm.course_add(code, code, credit, 'Lin', sections, '40')
        self.clear_output()

    def add_student(self, courses: str, student_id: str = 'S001'):
        dm.student_add(student_id, 'Ana', 'CS1', courses)
        self.clear_output()

    # Normal cases

    def test_build_schedule_marks_every_slot(self):
        self.add_course('CS101', '13,14@R101;2a@R205')
        self.add_student('CS101')
        table = sc.build_schedule('S001')
        self.assertEqual(len(table), 7 * 12)
        self.assertEqual(table['13'], ['CS101'])
        self.assertEqual(table['14'], ['CS101'])
        self.assertEqual(table['2a'], ['CS101'])
        self.assertEqual(table['15'], [])

    def test_course_meeting_several_times_shows_in_all_slots(self):
        self.add_course('CS101', '13,14@R101;35,36@R102')
        self.add_student('CS101')
        table = sc.build_schedule('S001')
        occupied = [t for t, codes in table.items() if codes]
        self.assertEqual(sorted(occupied), ['13', '14', '35', '36'])

    def test_two_courses_same_day(self):
        self.add_course('CS101', '13,14@R101')
        self.add_course('MA101', '16,17@R102')
        self.add_student('CS101,MA101')
        table = sc.build_schedule('S001')
        self.assertEqual(table['13'], ['CS101'])
        self.assertEqual(table['16'], ['MA101'])
        self.assertEqual(sc.find_conflicts(table), [])

    def test_schedule_prints_grid(self):
        self.add_course('CS101', '13@R101')
        self.add_student('CS101')
        sc.schedule('S001')
        lines = self.output().splitlines()
        self.assertIn('Mon', lines[0])
        self.assertIn('Sun', lines[0])
        self.assertEqual(len(lines), 13)  # header + 12 periods
        self.assertIn('CS101', lines[3])  # period 3

    def test_schedule_filters(self):
        self.add_course('CS101', '13,14@R101')
        self.add_student('CS101')
        sc.schedule('S001', 'course', 'CS101')
        self.assertEqual(self.output(), 'Mon 3: CS101\nMon 4: CS101\n')
        self.clear_output()
        sc.schedule('S001', 'period', '3')
        self.assertIn('Mon 3: CS101', self.output())
        self.assertIn('Tue 3: -', self.output())
        self.clear_output()
        sc.schedule('S001', 'day', '1')
        self.assertEqual(len(self.output().splitlines()), 12)

    def test_free_blocks_three_consecutive_periods(self):
        self.add_course('CS101', '14@R101')
        self.add_student('CS101')
        table = sc.build_schedule('S001')
        # Monday period 4 is taken; free: 1-3 and 5-c
        blocks = sc.find_free_blocks(table, '1', '1', 'c', 3)
        self.assertEqual(blocks, [('1', '1', '3'), ('1', '5', 'c')])
        blocks = sc.find_free_blocks(table, '1', '3', '5', 3)
        self.assertEqual(blocks, [])
        blocks = sc.find_free_blocks(table, '1', '3', '5', 1)
        self.assertEqual(blocks, [('1', '3', '3'), ('1', '5', '5')])

    def test_free_command_across_days(self):
        self.add_course('CS101', '13,14,15@R101')
        self.add_student('CS101')
        sc.free('S001', '*', '3', '5', '3')
        out = self.output().splitlines()
        self.assertNotIn('Mon', ' '.join(out))  # Monday 3-5 is full
        self.assertEqual(len(out), 6)  # Tue..Sun
        self.assertEqual(out[0], 'Tue 3-5 (3 periods free)')

    def test_stats(self):
        self.add_course('CS101', '13,14@R101', '3')
        self.add_course('MA101', '16,2a@R102', '4')
        self.add_student('CS101,MA101')
        sc.schedule_stats('S001')
        out = self.output()
        self.assertIn('Mon: 3 class periods, 9 free', out)
        self.assertIn('Tue: 1 class periods, 11 free', out)
        self.assertIn('Wed: 0 class periods, 12 free', out)
        self.assertIn('Total class periods: 4', out)
        self.assertIn('Total free periods: 80', out)
        self.assertIn('Weekly credits: 7', out)

    # Boundary cases

    def test_first_and_last_slot(self):
        self.add_course('CS101', '11,7c@R101')
        self.add_student('CS101')
        table = sc.build_schedule('S001')
        self.assertEqual(table['11'], ['CS101'])
        self.assertEqual(table['7c'], ['CS101'])

    def test_empty_schedule(self):
        self.add_student('')
        table = sc.build_schedule('S001')
        self.assertTrue(all(codes == [] for codes in table.values()))
        sc.schedule_stats('S001')
        self.assertIn('Weekly credits: 0', self.output())
        self.assertIn('Total free periods: 84', self.output())

    def test_free_whole_day_when_empty(self):
        self.add_student('')
        sc.free('S001', '3', '1', 'c')
        self.assertEqual(self.output(), 'Wed 1-c (12 periods free)\n')

    def test_free_single_period_range(self):
        self.add_student('')
        sc.free('S001', '1', '5', '5')
        self.assertEqual(self.output(), 'Mon 5-5 (1 periods free)\n')

    def test_course_taking_all_periods_of_a_day(self):
        self.add_course('CS101', '11,12,13,14,15,16,17,18,19,1a,1b,1c@R101')
        self.add_student('CS101')
        sc.free('S001', '1', '1', 'c')
        self.assertEqual(self.output(), 'Not found\n')

    # Conflicts

    def test_conflict_is_shown_not_hidden(self):
        self.add_course('CS101', '13,14@R101')
        self.add_course('MA101', '14,15@R102')
        self.add_student('CS101,MA101')
        table = sc.build_schedule('S001')
        self.assertEqual(table['14'], ['CS101', 'MA101'])
        self.assertEqual(sc.find_conflicts(table), [('14', ['CS101', 'MA101'])])
        sc.schedule('S001')
        out = self.output()
        self.assertIn('CS101/MA101', out)
        self.assertIn('Mon 4 衝堂：CS101 與 MA101', out)

    def test_conflicts_are_sorted_by_day_and_period(self):
        self.add_course('CS101', '25,13@R101')
        self.add_course('MA101', '25,13@R102')
        self.add_student('CS101,MA101')
        times = [t for t, _ in sc.find_conflicts(sc.build_schedule('S001'))]
        self.assertEqual(times, ['13', '25'])

    # Error cases

    def test_unknown_student(self):
        for call in (lambda: sc.schedule('NOPE'),
                     lambda: sc.free('NOPE', '1', '1', '3'),
                     lambda: sc.schedule_stats('NOPE')):
            self.assertRaises(CommandError, call)

    def test_schedule_errors(self):
        self.add_student('')
        self.assertRaises(CommandError, sc.schedule, 'S001', 'day', '8')
        self.assertRaises(CommandError, sc.schedule, 'S001', 'period', 'd')
        self.assertRaises(CommandError, sc.schedule, 'S001', 'color', 'red')
        self.assertRaises(CommandError, sc.schedule, 'S001', 'day')

    def test_free_errors(self):
        self.add_student('')
        self.assertRaises(CommandError, sc.free, 'S001', '8', '1', '3')
        self.assertRaises(CommandError, sc.free, 'S001', '1', '0', '3')
        self.assertRaises(CommandError, sc.free, 'S001', '1', '1', 'd')
        self.assertRaises(CommandError, sc.free, 'S001', '1', '5', '3')
        self.assertRaises(CommandError, sc.free, 'S001', '1', '1', '3', '0')
        self.assertRaises(CommandError, sc.free, 'S001', '1', '1', '3', 'x')

    def test_deleted_course_is_ignored(self):
        self.add_course('CS101', '13@R101')
        self.add_student('CS101')
        del dm.courses['CS101']
        table = sc.build_schedule('S001')
        self.assertTrue(all(codes == [] for codes in table.values()))


if __name__ == '__main__':
    unittest.main()
