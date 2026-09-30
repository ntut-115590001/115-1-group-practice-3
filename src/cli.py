from collections.abc import Callable

commands: dict[str, Callable] = {}

def command(name: str):
	def decorator(func: Callable):
		assert name not in commands, f"Command already exists: {name}"
		commands[name] = func
	return decorator

class CommandError(Exception):
	pass

def execute(name: str, args: list[str]):
	try:
		func = commands.get(name)
		if func is None:
			raise CommandError(f"Unknown command: {name}")
		func(*args)

	except CommandError as err:
		print(f'Error: {err}')