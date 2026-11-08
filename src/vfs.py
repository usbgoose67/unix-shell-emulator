"""Загрузка и изменение виртуальной файловой системы в памяти."""

import getpass
import posixpath
from dataclasses import dataclass, field
from pathlib import Path


ROOT_PATH = "/"


@dataclass
class VirtualFileSystem:
    """Файлы, каталоги и владельцы виртуальных объектов."""

    directories: set[str] = field(default_factory=lambda: {ROOT_PATH})
    files: dict[str, bytes] = field(default_factory=dict)
    owners: dict[str, str] = field(default_factory=dict)

    @property
    def directory_count(self):
        """Вернуть количество виртуальных каталогов."""
        return len(self.directories)

    @property
    def file_count(self):
        """Вернуть количество виртуальных файлов."""
        return len(self.files)

    def has_directory(self, path):
        """Проверить наличие каталога."""
        return path in self.directories

    def has_file(self, path):
        """Проверить наличие файла."""
        return path in self.files

    def read_file(self, path):
        """Прочитать байты виртуального файла."""
        return self.files[path]

    def owner_of(self, path):
        """Получить владельца виртуального объекта."""
        return self.owners[path]

    def change_owner(self, path, owner, recursive=False):
        """Изменить владельца объекта и при необходимости потомков."""
        if path not in self.owners:
            raise ValueError(f"объект не найден: {path}")
        self.owners[path] = owner
        if recursive and path in self.directories:
            prefix = path.rstrip("/") + "/"
            for child in self.owners:
                if child.startswith(prefix):
                    self.owners[child] = owner

    def copy(self, source, destination, recursive=False):
        """Скопировать файл или каталог в памяти."""
        if source not in self.owners:
            raise ValueError(f"источник не найден: {source}")
        target = self._target_path(source, destination)
        if source in self.files:
            self._copy_file(source, target)
            return
        if not recursive:
            raise ValueError("для каталога требуется ключ -r")
        if target == source or (
            source != ROOT_PATH
            and target.startswith(source.rstrip("/") + "/")
        ):
            raise ValueError("нельзя копировать каталог внутрь себя")
        self._copy_directory(source, target)

    def _target_path(self, source, destination):
        """Определить конечное имя объекта копирования."""
        if destination in self.directories:
            name = posixpath.basename(source.rstrip("/"))
            return posixpath.join(destination, name)
        return destination

    def _copy_file(self, source, target):
        """Скопировать байты и владельца файла."""
        if target in self.directories:
            raise ValueError(f"назначение является каталогом: {target}")
        parent = posixpath.dirname(target)
        if parent not in self.directories:
            raise ValueError(f"родительский каталог не найден: {parent}")
        self.files[target] = self.files[source]
        self.owners[target] = self.owners[source]

    def _copy_directory(self, source, target):
        """Создать копию каталога и всех его потомков."""
        if target in self.owners:
            raise ValueError(f"назначение уже существует: {target}")
        parent = posixpath.dirname(target)
        if parent not in self.directories:
            raise ValueError(f"родительский каталог не найден: {parent}")
        prefix = source.rstrip("/") + "/"
        dirs = sorted(self.directories)
        files = list(self.files.items())
        self.directories.add(target)
        self.owners[target] = self.owners[source]
        for directory in dirs:
            if directory.startswith(prefix):
                new_path = posixpath.join(
                    target, directory[len(prefix):]
                )
                self.directories.add(new_path)
                self.owners[new_path] = self.owners[directory]
        for path, content in files:
            if path.startswith(prefix):
                new_path = posixpath.join(target, path[len(prefix):])
                self.files[new_path] = content
                self.owners[new_path] = self.owners[path]


def load_vfs(source_path):
    """Загрузить директорию с диска в память без изменений."""
    source = Path(source_path)
    if not source.is_dir() or source.is_symlink():
        raise ValueError("директория VFS не найдена")
    vfs = VirtualFileSystem()
    vfs.owners[ROOT_PATH] = getpass.getuser()
    _load_directory(source, source, vfs)
    return vfs


def _load_directory(source, current, vfs):
    """Рекурсивно считать объекты без записи на диск."""
    try:
        for entry in sorted(current.iterdir()):
            if entry.is_symlink():
                raise ValueError("символические ссылки не поддерживаются")
            relative = entry.relative_to(source).as_posix()
            virtual_path = f"/{relative}"
            if entry.is_dir():
                vfs.directories.add(virtual_path)
                _load_directory(source, entry, vfs)
            elif entry.is_file():
                vfs.files[virtual_path] = entry.read_bytes()
            else:
                raise ValueError("неподдерживаемый тип файла")
            vfs.owners[virtual_path] = getpass.getuser()
    except OSError as error:
        raise ValueError(f"ошибка чтения VFS: {error}") from error


def format_vfs_info(vfs):
    """Подготовить сведения о загруженной VFS."""
    return (
        "Виртуальная файловая система загружена.\n"
        f"Каталогов: {vfs.directory_count}\n"
        f"Файлов: {vfs.file_count}"
    )
