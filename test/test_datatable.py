import tempfile
import unittest
from io import StringIO
from pathlib import Path
from typing import cast
from unittest.mock import patch

from src import cli
from src import datatable
from src.datatable import Datatable


class DatatableTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_path = Path(self.temp_dir.name) / 'data'
        self.data_path.mkdir()
        self.datapath_patcher = patch.object(datatable, 'DATAPATH', self.data_path)
        self.datapath_patcher.start()
        self.previous_datatables = Datatable.datatables
        Datatable.datatables = cast(dict[str, Datatable], {})

    def tearDown(self):
        Datatable.datatables = self.previous_datatables
        self.datapath_patcher.stop()
        self.temp_dir.cleanup()

    def test_new_table(self):
        table = Datatable('people', ('name', 'age'))

        self.assertEqual(table, {})
        self.assertEqual(table.name, 'people')
        self.assertEqual(table.fieldnames, ('name', 'age'))
        self.assertIs(Datatable.datatables['people'], table)

    def test_existing_csv(self):
        (self.data_path / 'people.csv').write_text('1,Ada,36\n2,Bob,42\n')

        table = Datatable('people', ('name', 'age'))

        self.assertEqual(table, {'1': {'name': 'Ada', 'age': '36'}, '2': {'name': 'Bob', 'age': '42'}})

        with self.assertRaisesRegex(ValueError, 'people'):
            Datatable('people', ('name',))

    def test_load(self):
        table = Datatable('people', ('name', 'age'))
        table.new_row('old', {'name': 'Old', 'age': '1'})
        (self.data_path / 'people.csv').write_text('1,Ada,36\n2,,42')

        table.load()
        self.assertEqual(table, {'1': {'name': 'Ada', 'age': '36'}, '2': {'age': '42'}})

        (self.data_path / 'people.csv').unlink()

        self.assertRaises(Exception, table.load)

    def test_save(self):
        table = Datatable('people', ('name', 'age'))
        table.new_row('1', {'name': 'Ada', 'age': '36'})
        table.new_row('2', {'name': 'Bob', 'age': '42'})

        table.save()

        self.assertTrue(table.path.exists())
        self.assertEqual(table.path.read_text(), '1,Ada,36\n2,Bob,42\n')

    def test_new_row(self):
        (self.data_path / 'people.csv').write_text('1,Ada,36\n2,Bob,42\n')
        table = Datatable('people', ('name', 'age'))

        table['1']['name'] = 'Leo'
        self.assertEqual(table['1']['name'], 'Leo')
        self.assertEqual(table.new_row('3', { 'age': '18' })['age'], '18')
        with self.assertRaises(ValueError):
            table['1']['names'] = 'Leo'
        self.assertRaises(ValueError, table.new_row, '1', { 'age': '18' })
        self.assertRaises(ValueError, table.new_row, '4', { 'ages': '18' })

    def test_save_all(self):
        (self.data_path / 'first.csv').write_text('1,A\n')
        (self.data_path / 'second.csv').write_text('1,B\n')
        first = Datatable('first', ('value',))
        second = Datatable('second', ('value',))
        first.clear()
        second['1'].update({'value': 'A'})

        Datatable.save_all()

        self.assertEqual((self.data_path / 'first.csv').read_text(), '')
        self.assertEqual((self.data_path / 'second.csv').read_text(), '1,A\n')

    @patch('sys.stdout', new_callable=StringIO)
    def test_command_datatable_list(self, mock_stdout: StringIO):
        Datatable('first', ('value',))
        Datatable('second', ('value',))

        datatable.datatable('list')
        self.assertIn('first', mock_stdout.getvalue())
        self.assertIn('second', mock_stdout.getvalue())

        with self.assertRaises(cli.CommandError):
            datatable.datatable('list', 'extra')

    @patch('sys.stdout', new_callable=StringIO)
    def test_command_datatable_print(self, mock_stdout: StringIO):
        table = Datatable('people', ('name', 'age'))
        table.new_row('1', {'name': 'Ada', 'age': '36'})
        table.new_row('2', {'name': 'Bob', 'age': '42'})

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
        table = Datatable('people', ('name', 'age'))
        table2 = Datatable('people2', ('name', 'age'))

        with patch.object(table, 'save') as mock_save, patch.object(table2, 'save') as mock_save2:
            datatable.datatable('save')
            mock_save.assert_called_once()
            mock_save2.assert_called_once()

        with patch.object(table, 'save') as mock_save, patch.object(table2, 'save') as mock_save2:
            datatable.datatable('save', 'people')
            mock_save.assert_called_once()
            mock_save2.assert_not_called()

        self.assertRaises(cli.CommandError, datatable.datatable, 'save', 'nonexistent')
        self.assertIs(datatable.datatable('save', 'people'), cli.Result.SUCCESS)

    @patch('sys.stdout', new_callable = StringIO)
    def test_command_datatable_reload(self, mock_stdout: StringIO):
        table = Datatable('people', ('name', 'age'))
        table2 = Datatable('people2', ('name', 'age'))

        with patch.object(table, 'load') as mock_save, patch.object(table2, 'load') as mock_save2:
            datatable.datatable('reload')
            mock_save.assert_called_once()
            mock_save2.assert_called_once()

        with patch.object(table, 'load') as mock_save, patch.object(table2, 'load') as mock_save2:
            datatable.datatable('reload', 'people')
            mock_save.assert_called_once()
            mock_save2.assert_not_called()

        (self.data_path / 'nonexistent.csv').write_text('')
        (self.data_path / 'people2.csv').write_text('')
        self.assertRaises(cli.CommandError, datatable.datatable, 'reload', 'nonexistent')
        self.assertRaises(cli.CommandError, datatable.datatable, 'reload', 'people')
        self.assertIs(datatable.datatable('reload', 'people2'), cli.Result.SUCCESS)

    def test_command_other(self):
        self.assertRaises(cli.CommandError, datatable.datatable, 'nonexistent')