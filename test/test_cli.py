from io import StringIO
import unittest
from unittest.mock import Mock, patch
import src.cli as cli

class TestCli(unittest.TestCase):
	def setUp(self) -> None:
		self.commands = cli.commands.copy()
		self.descriptions = cli.descriptions.copy()

	def tearDown(self) -> None:
		cli.commands = self.commands.copy()
		cli.descriptions = self.descriptions.copy()

	def test_commandWrap(self):
		@cli.command('zero')
		def zero():
			pass
		self.assertIs(zero(), cli.Result.SUCCESS)
		self.assertRaises(cli.CommandError, zero, '1')

		@cli.command('one')
		def one(one: str):
			pass
		self.assertRaises(cli.CommandError, one)
		self.assertIs(one('1'), cli.Result.SUCCESS)
		self.assertRaises(cli.CommandError, one, '1', '2')

		@cli.command('one-or-two')
		def oneOrTwo(one: str, two: str | None = None):
			pass
		self.assertRaises(cli.CommandError, oneOrTwo)
		self.assertIs(oneOrTwo('1'), cli.Result.SUCCESS)
		self.assertIs(oneOrTwo('1', '2'), cli.Result.SUCCESS)
		self.assertRaises(cli.CommandError, oneOrTwo, '1', '2', '3')
		
		@cli.command('unlimit')
		def unlimit(*args: str):
			pass
		self.assertIs(unlimit(), cli.Result.SUCCESS)
		self.assertIs(unlimit('1'), cli.Result.SUCCESS)
		self.assertIs(unlimit('1', '2'), cli.Result.SUCCESS)

		@cli.command('internal')
		def internal():
			def test(arg: str):
				pass
			test(*[])
		self.assertRaises(cli.CommandError, internal, '1')
		self.assertRaises(TypeError, internal)

		@cli.command('return-value')
		def returnValue():
			return cli.Result.EXIT
		self.assertIs(returnValue(), cli.Result.EXIT)

	def test_commandRegister(self):
		@cli.command('foo')
		def foo():
			"""foo is not bar"""
			pass
		self.assertIs(cli.commands['foo'], foo)
		self.assertEqual(cli.descriptions['foo'], "foo is not bar")

		with self.assertRaises(Exception):
			@cli.command('foo')
			def foo():
				pass

	def test_execute(self):
		mock = Mock(return_value = None)
		@cli.command('foo-bar')
		def fooBar(arg: str):
			return mock(arg)
		self.assertRaises(cli.CommandError, cli.execute, 'foo-bar "test\\"')
		self.assertRaises(cli.CommandError, cli.execute, 'non-existent')
		self.assertRaises(cli.CommandError, cli.execute, 'foo-bar')
		self.assertIs(cli.Result.SUCCESS, cli.execute('foo-bar content'))
		mock.assert_called_once_with('content')
		self.assertIs(cli.Result.SUCCESS, cli.execute(r"""foo-bar "con\"tent" """))
		mock.assert_called_with(r'con"tent')
		self.assertIs(cli.Result.SUCCESS, cli.execute(r"""foo-bar 'con\\"tent'"""))
		mock.assert_called_with(r'con\\"tent')
		mock.return_value = cli.Result.EXIT
		self.assertIs(cli.Result.EXIT, cli.execute('foo-bar ~'))
		mock.side_effect = cli.CommandError
		self.assertRaises(cli.CommandError, cli.execute, 'foo-bar content')

		self.assertIs(cli.Result.NONE, cli.execute(''))

	@patch('sys.stdout', new_callable = StringIO)
	def test_run(self, mockStdout: StringIO):
		@cli.command('example')
		def example(err: str | None = None):
			if err is not None:
				raise cli.CommandError('custom error!')

		self.assertIs(cli.Result.ERROR, cli.run('example true'))
		self.assertIs(cli.Result.SUCCESS, cli.run('example'))
		self.assertRegex(mockStdout.getvalue(), 'custom error!')

	def test_help(self):
		@cli.command('cmd-a')
		def cmdA():
			"""Foo is not bar.

			...or, is it?
			"""
			pass

		@cli.command('cmd-b')
		def cmdB():
			"""Bar is foo."""
			pass

		@cli.command('mystery')
		def mystery():
			pass

		with patch('sys.stdout', new_callable = StringIO) as mockStdout:
			cli.help()
			output = mockStdout.getvalue()
			for text in ('cmd-a', 'cmd-b', 'mystery', 'Foo is not bar.', 'Bar is foo.'):
				self.assertRegex(output, text)
			self.assertNotRegex(output, '...or, is it?')

		for (cmd, doc) in (
			('cmd-a', 'Foo is not bar.\n\n...or, is it?'),
			('cmd-b', 'Bar is foo.'),
			('mystery', None),
			):
			with patch('sys.stdout', new_callable = StringIO) as mockStdout:
				cli.help(cmd)
				if doc:
					self.assertRegex(mockStdout.getvalue(), doc)

	@patch('sys.stdout', new_callable = StringIO)
	def test_exit(self, mockStdout: StringIO):
		self.assertIs(cli.Result.EXIT, cli.exit())
