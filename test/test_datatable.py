import tempfile
import unittest
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from src import cli
from src import datatable
from src.datatable import Datatable


@dataclass
class Person:
    name: str
    age: int


def person_from_row(fields: list[str]) -> Person:
    return Person(fields[0], int(fields[1]))


def person_to_row(person: Person) -> list[str]:
    return [person.name, str(person.age)]


class DatatableTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_path = Path(self.temp_dir.name) / 'data'
        self.data_path.mkdir()
        self.datapath_patcher = patch.object(datatable, 'DATAPATH', self.data_path)
        self.datapath_patcher.start()
        self.previous_datatables = Datatable.datatables
        Datatable.datatables = {}

    def tearDown(self):
        Datatable.datatables = self.previous_datatables
        self.datapath_patcher.stop()
        self.temp_dir.cleanup()

    def make_table(self, name: str = 'people') -> Datatable[Person]:
        return Datatable(name, person_from_row, person_to_row)

    def test_new_table(self):
        table = self.make_table()

        self.assertEqual(table, {})
        self.assertEqual(table.name, 'people')
        self.assertEqual(table.path, self.data_path / 'people.csv')
        self.assertIs(Datatable.datatables['people'], table)

        self.assertRaisesRegex(ValueError, 'people', self.make_table)

    def test_existing_csv(self):
        (self.data_path / 'people.csv').write_text('1,Ada,36\n2,Bob,42\n')

        table = self.make_table()

        self.assertEqual(table, {'1': Person('Ada', 36), '2': Person('Bob', 42)})

    def test_load_replaces_existing_data(self):
        table = self.make_table()
        table['old'] = Person('Old', 1)
        (self.data_path / 'people.csv').write_text('1,Ada,36\n2,Bob,42\n')

        table.load()

        self.assertEqual(table, {'1': Person('Ada', 36), '2': Person('Bob', 42)})

        (self.data_path / 'people.csv').unlink()
        self.assertRaises(FileNotFoundError, table.load)

    def test_save(self):
        table = self.make_table()
        table['1'] = Person('Ada', 36)
        table['2'] = Person('Bob', 42)

        table.save()

        self.assertTrue(table.path.exists())
        self.assertEqual(table.path.read_text(), '1,Ada,36\n2,Bob,42\n')

    def test_dictionary_operations(self):
        table = self.make_table()
        table['1'] = Person('Ada', 36)
        table.update({'2': Person('Grace', 37)})

        self.assertEqual(table['1'], Person('Ada', 36))
        self.assertEqual(table['2'], Person('Grace', 37))
        self.assertRaises(KeyError, lambda: table['3'])
        del table['1']
        self.assertNotIn('1', table)

    def test_save_all(self):
        (self.data_path / 'first.csv').write_text('1,A,36\n')
        (self.data_path / 'second.csv').write_text('1,B,42\n')
        first = self.make_table('first')
        second = self.make_table('second')
        first.clear()
        second['1'] = Person('Bob', 42)

        Datatable.save_all()

        self.assertEqual((self.data_path / 'first.csv').read_text(), '')
        self.assertEqual((self.data_path / 'second.csv').read_text(), '1,Bob,42\n')

    @patch('sys.stdout', new_callable=StringIO)
    def test_command_datatable_list(self, mock_stdout: StringIO):
        self.make_table('first')
        self.make_table('second')

        datatable.datatable('list')
        self.assertIn('first', mock_stdout.getvalue())
        self.assertIn('second', mock_stdout.getvalue())

        self.assertRaises(cli.CommandError, datatable.datatable, 'list', 'extra')

    @patch('sys.stdout', new_callable=StringIO)
    def test_command_datatable_print(self, mock_stdout: StringIO):
        table = self.make_table()
        table['1'] = Person('Ada', 36)
        table['2'] = Person('Bob', 42)

        datatable.datatable('print', 'people')
        output = mock_stdout.getvalue()
        self.assertIn('name', output)
        self.assertIn('Ada', output)
        self.assertIn('42', output)
        self.assertIn('1', output)

        self.assertRaises(cli.CommandError, datatable.datatable, 'print')
        self.assertRaises(cli.CommandError, datatable.datatable, 'print', 'nonexistent')

    @patch('sys.stdout', new_callable=StringIO)
    def test_command_datatable_save(self, mock_stdout: StringIO):
        first = self.make_table('first')
        second = self.make_table('second')

        with patch.object(first, 'save') as mock_save, patch.object(second, 'save') as mock_save2:
            self.assertIs(datatable.datatable('save'), cli.Result.SUCCESS)
            mock_save.assert_called_once()
            mock_save2.assert_called_once()

        with patch.object(first, 'save') as mock_save, patch.object(second, 'save') as mock_save2:
            datatable.datatable('save', 'first')
            mock_save.assert_called_once()
            mock_save2.assert_not_called()

        self.assertRaises(cli.CommandError, datatable.datatable, 'save', 'nonexistent')
        self.assertIs(datatable.datatable('save', 'first'), cli.Result.SUCCESS)

    @patch('sys.stdout', new_callable=StringIO)
    def test_command_datatable_reload(self, mock_stdout: StringIO):
        first = self.make_table('first')
        second = self.make_table('second')

        with patch.object(first, 'load') as mock_load, patch.object(second, 'load') as mock_load2:
            datatable.datatable('reload')
            mock_load.assert_called_once()
            mock_load2.assert_called_once()

        with patch.object(first, 'load') as mock_load, patch.object(second, 'load') as mock_load2:
            datatable.datatable('reload', 'first')
            mock_load.assert_called_once()
            mock_load2.assert_not_called()

        (self.data_path / 'second.csv').write_text('')
        self.assertRaises(cli.CommandError, datatable.datatable, 'reload', 'nonexistent')
        self.assertRaises(cli.CommandError, datatable.datatable, 'reload', 'first')
        self.assertIs(datatable.datatable('reload', 'second'), cli.Result.SUCCESS)

    def test_command_other(self):
        self.assertRaises(cli.CommandError, datatable.datatable, 'nonexistent')