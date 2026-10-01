import unittest
import src.cli as cli

class TestCli(unittest.TestCase):
	def setUp(self) -> None:
		self.commands = cli.commands.copy()
		self.descriptions = cli.descriptions.copy()

	def tearDown(self) -> None:
		cli.commands = self.commands.copy()
		cli.descriptions = self.descriptions.copy()

	def test_wrongArguementsNum(self):

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

	def test_commandRegister(self):
		@cli.command('foo')
		def foo():
			"""foo is not bar"""
			pass
		self.assertEqual(cli.commands['foo'], foo)
		self.assertEqual(cli.descriptions['foo'], "foo is not bar")

		with self.assertRaises(Exception):
			@cli.command('foo')
			def foo():
				pass
