"""Разбор и выполнение команд эмулятора."""

import os
import re
import shlex
from dataclasses import dataclass


VARIABLE_PATTERN = re.compile(r"\$(\w+|\{[^}]+\})")


@dataclass(frozen=True)
class CommandResult:
    """Результат выполнения одной команды."""

    output: str
    should_exit: bool = False
    is_error: bool = False


def expand_variables(value):
    """Раскрыть переменные окружения в аргументе."""

    def replace_variable(match):
        """Получить значение переменной окружения."""
        name = match.group(1).strip("{}")
        return os.environ.get(name, "")

    return VARIABLE_PATTERN.sub(replace_variable, value)


def parse_command(line):
    """Разделить команду и аргументы, раскрыв переменные."""
    try:
        parts = shlex.split(line, posix=False)
    except ValueError as error:
        raise ValueError("некорректные кавычки") from error

    cleaned = [part.strip('"') for part in parts]
    return [expand_variables(part) for part in cleaned]


def execute_command(line):
    """Выполнить команду и вернуть результат."""
    try:
        parts = parse_command(line)
    except ValueError as error:
        return CommandResult(f"Ошибка: {error}", is_error=True)

    if not parts:
        return CommandResult("")

    command, *arguments = parts
    if command == "exit":
        if arguments:
            return CommandResult(
                "Ошибка: exit не принимает аргументы",
                is_error=True,
            )
        return CommandResult("Завершение работы", should_exit=True)

    if command in ("ls", "cd"):
        return CommandResult(f"{command}: аргументы: {arguments}")

    return CommandResult(
        f"Ошибка: неизвестная команда '{command}'",
        is_error=True,
    )
