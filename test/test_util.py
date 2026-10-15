import unittest

from src.util import split_map, bool_to_str, join_map, escape_tab

class TestUtil(unittest.TestCase):
    def test_split_map_and_join_map(self):
        self.assertEqual(split_map(join_map(['a', 'b', 'c'])), ['a', 'b', 'c'])
        self.assertEqual(split_map(join_map([])), [])
        self.assertEqual(split_map(join_map([1, 2, 3], str), int), [1, 2, 3])
        self.assertEqual(split_map(join_map(['a', 'b', 'c'], sep=','), sep=','), ['a', 'b', 'c'])
        self.assertRaises(ValueError, join_map, ['a', 'b', 'c,d'], sep=',')

    def test_bool_to_str(self):
        self.assertEqual(bool(bool_to_str(True)), True)
        self.assertEqual(bool(bool_to_str(False)), False)

    def test_escape_tab(self):
        self.assertEqual(escape_tab('a\tb'), 'a b')
        self.assertEqual(escape_tab('cd'), 'cd')
        self.assertEqual(escape_tab('e\tf\tg'), 'e f g')