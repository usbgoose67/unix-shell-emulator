"""Разбор и выполнение команд первого этапа эмулятора."""

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


def expand_variables(value):
    """Раскрыть переменные окружения в одном аргументе."""

    def replace_variable(match):
        """Получить значение найденной переменной окружения."""
        name = match.group(1).strip("{}")
        return os.environ.get(name, "")

    return VARIABLE_PATTERN.sub(replace_variable, value)


def parse_command(line):
    """Разделить команду на имя и аргументы с раскрытием переменных."""
    try:
        parts = shlex.split(line, posix=False)
    except ValueError as error:
        raise ValueError("некорректные кавычки") from error

    cleaned = [part.strip('"') for part in parts]
    return [expand_variables(part) for part in cleaned]


def execute_command(line):
    """Выполнить команду-заглушку или вернуть сообщение об ошибке."""
    try:
        parts = parse_command(line)
    except ValueError as error:
        return CommandResult(f"Ошибка: {error}")

    if not parts:
        return CommandResult("")

    command, *arguments = parts
    if command == "exit":
        if arguments:
            return CommandResult("Ошибка: exit не принимает аргументы")
        return CommandResult("Завершение работы", should_exit=True)

    if command in ("ls", "cd"):
        return CommandResult(f"{command}: аргументы: {arguments}")

    return CommandResult(f"Ошибка: неизвестная команда '{command}'")
