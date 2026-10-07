# pyright: reportPrivateUsage = false
import unittest
from io import StringIO
from unittest.mock import MagicMock, patch

from src import cli


class TestCli(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.commands = cli._commands.copy()

    def tearDown(self):
        cli._commands = TestCli.commands.copy()

    def test_command_wrap(self):
        @cli.command('zero')
        def zero():
            pass # pragma: no cover
        self.assertIs(zero(), cli.Result.SUCCESS)
        self.assertRaises(cli.CommandError, zero, '1')

        @cli.command('one')
        def one(one: str):
            pass # pragma: no cover
        self.assertRaises(cli.CommandError, one)
        self.assertIs(one('1'), cli.Result.SUCCESS)
        self.assertRaises(cli.CommandError, one, '1', '2')

        @cli.command('one-or-two')
        def oneOrTwo(one: str, two: str | None = None):
            pass # pragma: no cover
        self.assertRaises(cli.CommandError, oneOrTwo)
        self.assertIs(oneOrTwo('1'), cli.Result.SUCCESS)
        self.assertIs(oneOrTwo('1', '2'), cli.Result.SUCCESS)
        self.assertRaises(cli.CommandError, oneOrTwo, '1', '2', '3')
        
        @cli.command('unlimit')
        def unlimit(*args: str):
            pass # pragma: no cover
        self.assertIs(unlimit(), cli.Result.SUCCESS)
        self.assertIs(unlimit('1'), cli.Result.SUCCESS)
        self.assertIs(unlimit('1', '2'), cli.Result.SUCCESS)

        @cli.command('internal')
        def internal():
            def test(arg: str):
                pass # pragma: no cover
            test() # type: ignore
        self.assertRaises(cli.CommandError, internal, '1')
        self.assertRaises(TypeError, internal)

        @cli.command('return-value')
        def return_value():
            return cli.Result.EXIT
        self.assertIs(return_value(), cli.Result.EXIT)

    def test_command_register(self):
        @cli.command('foo')
        def foo():
            """foo is not bar"""
            pass # pragma: no cover
        self.assertIs(cli._commands['foo'], foo)

        with self.assertRaises(ValueError):
            @cli.command('foo')
            def foo():
                pass # pragma: no cover

    def test_execute(self):
        mock = MagicMock(return_value = None)
        @cli.command('foo-bar')
        def foo_bar(arg: str):
            return mock(arg)
        self.assertRaises(cli.CommandError, cli.execute, 'foo-bar "test\\"')
        self.assertRaises(cli.CommandError, cli.execute, 'non-existent')
        self.assertRaises(cli.CommandError, cli.execute, 'foo-bar')
        self.assertIs(cli.Result.SUCCESS, cli.execute('foo-bar content'))
        mock.assert_called_once_with('content')
        mock.reset_mock()
        self.assertIs(cli.Result.SUCCESS, cli.execute(r"""foo-bar "con\"tent" """))
        mock.assert_called_once_with(r'con"tent')
        mock.reset_mock()
        self.assertIs(cli.Result.SUCCESS, cli.execute(r"""foo-bar 'con\\"tent'"""))
        mock.assert_called_once_with(r'con\\"tent')
        mock.reset_mock()
        mock.return_value = cli.Result.EXIT
        self.assertIs(cli.Result.EXIT, cli.execute('foo-bar ~'))
        mock.side_effect = cli.CommandError
        self.assertRaises(cli.CommandError, cli.execute, 'foo-bar content')
        mock.side_effect = IndexError
        self.assertRaises(IndexError, cli.execute, 'foo-bar content')

        self.assertIs(cli.Result.NONE, cli.execute(''))
        self.assertIs(cli.Result.NONE, cli.execute('  \t '))

    @patch('sys.stdout', new_callable=StringIO)
    def test_run(self, mock_stdout: StringIO):
        @cli.command('example')
        def example(err: str | None = None):
            if err == 'true':
                raise cli.CommandError('custom error!')
            elif err is not None:
                [][1]
        self.assertIs(cli.Result.FAIL, cli.run('example true'))
        self.assertIn('custom error!', mock_stdout.getvalue())
        self.assertIs(cli.Result.SUCCESS, cli.run('example'))
        self.assertRaises(IndexError, cli.run, 'example false')

    def test_help(self):
        @cli.command('cmd-a')
        def cmd_a():
            """Foo is not bar.

            ...or, is it?
            """
            pass # pragma: no cover

        @cli.command('cmd-b')
        def cmd_b():
            """Bar is foo."""
            pass # pragma: no cover

        @cli.command('mystery')
        def mystery():
            pass # pragma: no cover

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            cli.help()
            output = mock_stdout.getvalue()
            for text in ('cmd-a', 'cmd-b', 'mystery', 'Foo is not bar.', 'Bar is foo.'):
                self.assertIn(text, output)
            self.assertNotIn('...or, is it?', output)

        for cmd, doc in (
            ('cmd-a', 'Foo is not bar.\n\n...or, is it?'),
            ('cmd-b', 'Bar is foo.'),
            ('mystery', None),
        ):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                cli.help(cmd)
                if doc:
                    self.assertIn(doc, mock_stdout.getvalue())
        
        self.assertRaises(cli.CommandError, cli.help, 'non-existent')

    @patch('sys.stdout', new_callable=StringIO)
    def test_exit(self, mock_stdout: StringIO):
        self.assertIs(cli.Result.EXIT, cli.exit())
