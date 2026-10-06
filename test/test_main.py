import unittest
from io import StringIO
from unittest.mock import Mock, call, patch

from src.cli import Result
from src.main import main

def _run(line: str):
    if line == 'Ctrl':
        raise KeyboardInterrupt
    if line == 'raise':
        raise Exception('Custom')
    if line == 'exit':
        return Result.EXIT

@patch('sys.stdout', StringIO())
@patch('src.datatable.Datatable.save_all')
@patch('src.cli.run', side_effect=_run)
class MainTests(unittest.TestCase):
    @patch('sys.stdin', StringIO('test\nAny thing\nexit\nother\n'))
    def test_exit_command(self, run: Mock, save_all: Mock):
        main()
        self.assertEqual(run.call_args_list, [call('test'), call('Any thing'), call('exit')])
        save_all.assert_called_once()

    @patch('sys.stdin', StringIO('test\nAny thing\n'))
    def test_EOF(self, run: Mock, save_all: Mock):
        main()
        self.assertEqual(run.call_args_list, [call('test'), call('Any thing')])
        save_all.assert_called_once()

    @patch('sys.stdin', StringIO('test\nAny thing\nCtrl\nnever\n'))
    def test_ctrl(self, run: Mock, save_all: Mock):
        main()
        self.assertEqual(run.call_args_list, [call('test'), call('Any thing'), call('Ctrl')])
        save_all.assert_called_once()

    @patch('sys.stdin', StringIO('test\nAny thing\nraise\nno\n'))
    def test_internal(self, run: Mock, save_all: Mock):
        self.assertRaisesRegex(Exception, 'Custom', main)
        self.assertEqual(run.call_args_list, [call('test'), call('Any thing'), call('raise')])
        save_all.assert_called_once()