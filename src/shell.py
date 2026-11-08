"""Разбор и выполнение команд UNIX-эмулятора."""

import getpass
import os
import posixpath
import re
import shlex
from dataclasses import dataclass


VARIABLE_PATTERN = re.compile(r"\$(\w+|\{[^}]+\})")
MAX_PATH_ARGUMENTS = 1
COPY_ARGUMENTS = 2
OWNER_ARGUMENTS = 2


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
            "cp": self.command_cp,
            "chown": self.command_chown,
        }
        handler = handlers.get(command)
        if handler is None:
            return error_result(f"неизвестная команда '{command}'")
        return handler(arguments)

    def command_ls(self, arguments):
        """Показать имена объектов или владельцев каталога."""
        if self.vfs is None:
            return CommandResult(f"ls: аргументы: {arguments}")
        detailed = bool(arguments and arguments[0] == "-l")
        paths = arguments[1:] if detailed else arguments
        if len(paths) > MAX_PATH_ARGUMENTS:
            return error_result("ls принимает не более одного пути")
        path = self.resolve_path(paths[0] if paths else ".")
        if self.vfs.has_file(path):
            return CommandResult(self._display_entry(path, detailed))
        if not self.vfs.has_directory(path):
            return error_result(f"каталог не найден: {path}")
        return CommandResult(self.list_directory(path, detailed))

    def _display_entry(self, path, detailed):
        """Сформировать строку вывода для одного объекта."""
        name = posixpath.basename(path)
        if self.vfs.has_directory(path):
            name += "/"
        if detailed:
            return f"{self.vfs.owner_of(path)}  {name}"
        return name

    def list_directory(self, path, detailed=False):
        """Получить отсортированные записи каталога."""
        paths = []
        for directory in self.vfs.directories:
            if directory != path and posixpath.dirname(directory) == path:
                paths.append(directory)
        for file_path in self.vfs.files:
            if posixpath.dirname(file_path) == path:
                paths.append(file_path)
        return "\n".join(
            self._display_entry(item, detailed)
            for item in sorted(paths, key=posixpath.basename)
        )

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
        """Вывести строки файла в обратном порядке."""
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

    def command_cp(self, arguments):
        """Копировать виртуальный файл или каталог."""
        recursive = bool(arguments and arguments[0] in ("-r", "-R"))
        paths = arguments[1:] if recursive else arguments
        if len(paths) != COPY_ARGUMENTS:
            return error_result("cp требует источник и назначение")
        if self.vfs is None:
            return error_result("VFS не загружена")
        source, destination = map(self.resolve_path, paths)
        try:
            self.vfs.copy(source, destination, recursive)
        except ValueError as error:
            return error_result(str(error))
        return CommandResult("")

    def command_chown(self, arguments):
        """Изменить виртуального владельца объекта."""
        recursive = bool(arguments and arguments[0] in ("-R", "-r"))
        values = arguments[1:] if recursive else arguments
        if len(values) != OWNER_ARGUMENTS:
            return error_result("chown требует владельца и путь")
        if self.vfs is None:
            return error_result("VFS не загружена")
        owner, raw_path = values
        if not owner.strip():
            return error_result("имя владельца не может быть пустым")
        try:
            self.vfs.change_owner(
                self.resolve_path(raw_path), owner, recursive
            )
        except ValueError as error:
            return error_result(str(error))
        return CommandResult("")


def execute_command(line):
    """Выполнить команду без постоянной сессии для совместимости."""
    return ShellSession().execute(line)