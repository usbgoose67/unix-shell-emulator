"""Разбор и выполнение команд UNIX-эмулятора."""

import getpass
import os
import posixpath
import re
import shlex
from dataclasses import dataclass


VARIABLE_PATTERN = re.compile(r"\$(\w+|\{[^}]+\})")

MAX_PATH_ARGUMENTS = 1


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


def error_result(message):
    """Создать результат с признаком ошибки."""
    return CommandResult(f"Ошибка: {message}", is_error=True)


class ShellSession:
    """Состояние командной оболочки и текущего каталога."""

    def __init__(self, vfs=None):
        """Сохранить VFS и установить корневой каталог."""
        self.vfs = vfs
        self.cwd = "/"

    def resolve_path(self, path):
        """Преобразовать путь в абсолютный путь VFS."""
        if path.startswith("/"):
            return posixpath.normpath(path)
        return posixpath.normpath(posixpath.join(self.cwd, path))

    def execute(self, line):
        """Разобрать и выполнить введённую команду."""
        try:
            parts = parse_command(line)
        except ValueError as error:
            return error_result(str(error))

        if not parts:
            return CommandResult("")

        command, *arguments = parts
        handlers = {
            "ls": self.command_ls,
            "cd": self.command_cd,
            "tac": self.command_tac,
            "whoami": self.command_whoami,
            "exit": self.command_exit,
        }
        handler = handlers.get(command)
        if handler is None:
            return error_result(f"неизвестная команда '{command}'")
        return handler(arguments)

    def command_ls(self, arguments):
        """Показать содержимое каталога или информацию о файле."""
        if self.vfs is None:
            return CommandResult(f"ls: аргументы: {arguments}")
        if len(arguments) > MAX_PATH_ARGUMENTS:
            return error_result("ls принимает не более одного пути")

        path = self.resolve_path(arguments[0] if arguments else ".")
        if self.vfs.has_file(path):
            return CommandResult(posixpath.basename(path))
        if not self.vfs.has_directory(path):
            return error_result(f"каталог не найден: {path}")

        return CommandResult(self.list_directory(path))

    def list_directory(self, path):
        """Получить отсортированные имена объектов каталога."""
        names = []
        for directory in self.vfs.directories:
            if directory != path and posixpath.dirname(directory) == path:
                names.append(posixpath.basename(directory) + "/")
        for file_path in self.vfs.files:
            if posixpath.dirname(file_path) == path:
                names.append(posixpath.basename(file_path))
        return "\n".join(sorted(names))

    def command_cd(self, arguments):
        """Изменить текущий каталог внутри VFS."""
        if self.vfs is None:
            return CommandResult(f"cd: аргументы: {arguments}")
        if len(arguments) > MAX_PATH_ARGUMENTS:
            return error_result("cd принимает не более одного пути")

        path = self.resolve_path(arguments[0] if arguments else "/")
        if not self.vfs.has_directory(path):
            return error_result(f"каталог не найден: {path}")

        self.cwd = path
        return CommandResult("")

    def command_tac(self, arguments):
        """Вывести строки текстового файла в обратном порядке."""
        if len(arguments) != MAX_PATH_ARGUMENTS:
            return error_result("tac требует ровно один путь к файлу")
        if self.vfs is None:
            return error_result("VFS не загружена")

        path = self.resolve_path(arguments[0])
        if not self.vfs.has_file(path):
            return error_result(f"файл не найден: {path}")

        try:
            content = self.vfs.read_file(path).decode("utf-8")
        except UnicodeDecodeError:
            return error_result("tac поддерживает только файлы UTF-8")

        return CommandResult("\n".join(reversed(content.splitlines())))

    def command_whoami(self, arguments):
        """Показать имя пользователя реальной ОС."""
        if arguments:
            return error_result("whoami не принимает аргументы")
        return CommandResult(getpass.getuser())

    def command_exit(self, arguments):
        """Завершить работу эмулятора."""
        if arguments:
            return error_result("exit не принимает аргументы")
        return CommandResult("Завершение работы", should_exit=True)


def execute_command(line):
    """Выполнить команду без постоянной сессии для совместимости."""
    return ShellSession().execute(line)
