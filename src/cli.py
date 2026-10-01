from collections.abc import Callable
from enum import Enum, auto
import functools
import shlex
import inspect

commands: dict[str, Callable] = {}
descriptions: dict[str, str | None] = {}

def command(name: str):
	def decorator(func: Callable):
		assert name not in commands, f"Command already exists: {name}"
		@functools.wraps(func)
		def newFunc(*args, **kwargs):
			try:
				inspect.signature(func).bind(*args, **kwargs)
			except TypeError as err:
				raise CommandError(f'參數數量錯誤：{err}') from err
			result = func(*args, **kwargs)
			return Result.SUCCESS if result is None else result
		commands[name] = newFunc
		descriptions[name] = func.__doc__
		return newFunc
	return decorator

class CommandError(Exception):
	pass

class Result(Enum):
	SUCCESS = auto()
	ERROR = auto()
	NONE = auto()
	EXIT = auto()

def execute(line: str) -> Result:
	try:
		args = shlex.split(line)
	except ValueError as err:
		raise CommandError(f"解析錯誤：{err}") from err
	if len(args) == 0:
		return Result.NONE
	name, args = args[0], args[1:]
	func = commands.get(name)
	if func is None:
		raise CommandError(f"未知指令：{name}")
	return func(*args)

def run(line: str) -> Result:
	try:
		return execute(line)
	except CommandError as err:
		print(f'\033[91m錯誤！{err}\033[0m')
		return Result.ERROR

@command('help')
def help(command: str | None = None):
	"""取得指令說明。語法：help [<指令名稱>]。

	當未指定目標指令時，將輸出可用指令清單，附帶各自的簡短說明。
	"""
	if command is not None:
		if command not in descriptions:
			raise CommandError(f"未知指令：{command}")
		desc = descriptions[command]
		print(desc.strip() if desc is not None else '缺乏關於該指令的說明。')
		return
	for k, v in descriptions.items():
		print(k, '-', v.strip().splitlines()[0] if v else '無說明。')

@command('exit')
def exit():
	"""退出系統，無參數。"""
	print('退出系統！')
	return Result.EXIT