"""Загрузка виртуальной файловой системы в память."""

from dataclasses import dataclass, field
from pathlib import Path


ROOT_PATH = "/"


@dataclass
class VirtualFileSystem:
    """Представление файлов и каталогов в оперативной памяти."""

    directories: set[str] = field(
        default_factory=lambda: {ROOT_PATH}
    )
    files: dict[str, bytes] = field(default_factory=dict)

    @property
    def directory_count(self):
        """Вернуть количество виртуальных каталогов."""
        return len(self.directories)

    @property
    def file_count(self):
        """Вернуть количество виртуальных файлов."""
        return len(self.files)

    def has_directory(self, path):
        """Проверить наличие каталога в памяти."""
        return path in self.directories

    def has_file(self, path):
        """Проверить наличие файла в памяти."""
        return path in self.files

    def read_file(self, path):
        """Вернуть содержимое виртуального файла."""
        return self.files[path]


def load_vfs(source_path):
    """Загрузить директорию с диска в оперативную память."""
    source = Path(source_path)

    if not source.is_dir() or source.is_symlink():
        raise ValueError("директория VFS не найдена")

    vfs = VirtualFileSystem()
    _load_directory(source, source, vfs)
    return vfs


def _load_directory(source, current, vfs):
    """Рекурсивно прочитать каталог без изменения его файлов."""
    try:
        entries = sorted(current.iterdir())
        for entry in entries:
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
    except OSError as error:
        raise ValueError(f"ошибка чтения VFS: {error}") from error


def format_vfs_info(vfs):
    """Подготовить краткие сведения о загруженной VFS."""
    return (
        "Виртуальная файловая система загружена.\n"
        f"Каталогов: {vfs.directory_count}\n"
        f"Файлов: {vfs.file_count}"
    )
