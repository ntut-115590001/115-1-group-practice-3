"""Implement a easy command-line interface system."""

import functools
import inspect
import shlex
from collections.abc import Callable
from enum import Enum, auto
from typing import ParamSpec


_commands: dict[str, Callable[..., Result]] = {}


class Result(Enum):
    """Return value of command functions.
    
    * SUCCESS - Default value.
    * NONE - No operation performed.
    * ERROR - Error occurred. Automatically be used if the function raises CommandError.
    * EXIT - Exit the system.
    """
    SUCCESS = auto()
    NONE = auto()
    FAIL = auto()
    EXIT = auto()


class CommandError(Exception):
    """Exception raised when a command fails."""
    pass


P = ParamSpec('P')
def command(name: str) -> Callable[[Callable[P, Result | None]], Callable[P, Result]]:
    """Register the function as a new command."""
    def decorator(func: Callable[P, Result | None]) -> Callable[P, Result]:
        if name in _commands:
            raise ValueError(f'Command already exists: {name}')
        @functools.wraps(func)
        def new_func(*args: P.args, **kwargs: P.kwargs) -> Result:
            try:
                inspect.signature(func).bind(*args, **kwargs)
            except TypeError as err:
                raise CommandError(f'參數數量錯誤：{err}') from err
            result = func(*args, **kwargs)
            return Result.SUCCESS if result is None else result
        _commands[name] = new_func
        return new_func
    return decorator


def execute(line: str) -> Result:
    """Parse the command and call the corresponding function."""
    try:
        args = shlex.split(line)
    except ValueError as err:
        raise CommandError(f'解析錯誤：{err}') from err
    if not args:
        return Result.NONE
    name, args = args[0], args[1:]
    func = _commands.get(name)
    if func is None:
        raise CommandError(f'未知指令：{name}')
    return func(*args)

def run(line: str) -> Result:
    """Parse the command and call the corresponding function, with handling CommandError."""
    try:
        return execute(line)
    except CommandError as err:
        print(f'\033[91m錯誤！{err}\033[0m')
        return Result.FAIL


@command('help')
def help(command: str | None = None):
    """取得指令說明。語法：help [<指令名稱>]。

    當未指定目標指令時，將輸出可用指令清單，附帶各自的簡短說明。
    """
    if command is not None:
        if command not in _commands:
            raise CommandError(f'未知指令：{command}')
        desc = inspect.getdoc(_commands[command])
        print(desc if desc is not None else '缺乏關於該指令的說明。')
        return
    for k, v in _commands.items():
        desc = inspect.getdoc(v)
        print(k, '-', desc.splitlines()[0] if desc is not None else '無說明。')

@command('exit')
def exit():
    """退出系統，無參數。"""
    print('退出系統！')
    return Result.EXIT