"""Проверки копирования и виртуальных владельцев."""

import getpass
import tempfile
import unittest
from pathlib import Path

from src.shell import ShellSession
from src.vfs import load_vfs


class StageFiveTests(unittest.TestCase):
    """Проверки новых команд и неизменности исходных данных."""

    def setUp(self):
        """Подготовить исходные файлы и виртуальную сессию."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "docs" / "nested").mkdir(parents=True)
        (self.root / "docs" / "nested" / "deep.txt").write_text(
            "one\ntwo\n", encoding="utf-8"
        )
        (self.root / "root.txt").write_bytes(b"original")
        self.session = ShellSession(load_vfs(self.root))

    def test_cp_file(self):
        """Копировать файл в корне."""
        self.assertFalse(self.session.execute("cp root.txt copy.txt").is_error)
        self.assertEqual(self.session.vfs.read_file("/copy.txt"), b"original")

    def test_cp_into_directory(self):
        """Копировать файл в существующий каталог."""
        self.session.execute("cp root.txt docs")
        self.assertTrue(self.session.vfs.has_file("/docs/root.txt"))

    def test_cp_overwrite_virtual_only(self):
        """Перезаписать виртуальный файл без записи на диск."""
        self.session.execute("cp root.txt copy.txt")
        self.session.vfs.files["/root.txt"] = b"changed"
        self.session.execute("cp root.txt copy.txt")
        self.assertEqual(self.session.vfs.read_file("/copy.txt"), b"changed")
        self.assertEqual((self.root / "root.txt").read_bytes(), b"original")

    def test_cp_directory_requires_flag(self):
        """Запретить копирование каталога без -r."""
        self.assertTrue(self.session.execute("cp docs backup").is_error)

    def test_cp_recursive(self):
        """Скопировать каталог вместе с вложенными объектами."""
        self.assertFalse(self.session.execute("cp -r docs backup").is_error)
        self.assertTrue(self.session.vfs.has_directory("/backup/nested"))
        self.assertTrue(self.session.vfs.has_file("/backup/nested/deep.txt"))

    def test_cp_directory_into_itself(self):
        """Запретить копирование каталога внутрь себя."""
        result = self.session.execute("cp -r docs docs/nested/new")
        self.assertTrue(result.is_error)
        self.assertFalse(self.session.vfs.has_directory("/docs/nested/new"))

    def test_cp_missing_source(self):
        """Проверить отсутствие источника."""
        self.assertTrue(self.session.execute("cp absent.txt copy.txt").is_error)

    def test_cp_missing_parent(self):
        """Проверить отсутствие родительского каталога."""
        result = self.session.execute("cp root.txt absent/copy.txt")
        self.assertTrue(result.is_error)

    def test_cp_arguments(self):
        """Проверить число аргументов cp."""
        self.assertTrue(self.session.execute("cp root.txt").is_error)

    def test_chown_file(self):
        """Изменить виртуального владельца файла."""
        self.session.execute("chown alice root.txt")
        self.assertEqual(self.session.vfs.owner_of("/root.txt"), "alice")

    def test_chown_directory_only(self):
        """Без -R изменять владельца только каталога."""
        self.session.execute("chown alice docs")
        self.assertEqual(self.session.vfs.owner_of("/docs"), "alice")
        self.assertEqual(
            self.session.vfs.owner_of("/docs/nested"), getpass.getuser()
        )

    def test_chown_recursive(self):
        """С -R изменить владельца всех вложенных объектов."""
        self.session.execute("chown -R bob docs")
        self.assertEqual(self.session.vfs.owner_of("/docs"), "bob")
        self.assertEqual(self.session.vfs.owner_of("/docs/nested"), "bob")
        self.assertEqual(
            self.session.vfs.owner_of("/docs/nested/deep.txt"), "bob"
        )

    def test_chown_missing(self):
        """Проверить ошибку отсутствующего объекта."""
        self.assertTrue(self.session.execute("chown alice missing").is_error)

    def test_chown_arguments(self):
        """Проверить число аргументов chown."""
        self.assertTrue(self.session.execute("chown alice").is_error)

    def test_ls_long(self):
        """Показать владельца с помощью ls -l."""
        self.session.execute("chown alice root.txt")
        result = self.session.execute("ls -l root.txt")
        self.assertEqual(result.output, "alice  root.txt")

    def test_copy_keeps_owner(self):
        """При копировании сохранять виртуального владельца."""
        self.session.execute("chown alice root.txt")
        self.session.execute("cp root.txt copy.txt")
        self.assertEqual(self.session.vfs.owner_of("/copy.txt"), "alice")

    def test_copy_recursive_keeps_owners(self):
        """Копировать владельцев вложенных объектов."""
        self.session.execute("chown alice docs/nested/deep.txt")
        self.session.execute("cp -r docs backup")
        self.assertEqual(
            self.session.vfs.owner_of("/backup/nested/deep.txt"), "alice"
        )

    def test_source_unchanged_after_chown(self):
        """Не менять реальные права или содержимое файла."""
        original = (self.root / "root.txt").stat()
        self.session.execute("chown alice root.txt")
        current = (self.root / "root.txt").stat()
        self.assertEqual(current.st_mode, original.st_mode)
        self.assertEqual(current.st_uid, original.st_uid)
        self.assertEqual((self.root / "root.txt").read_bytes(), b"original")

    def test_copy_root(self):
        """Проверить копирование виртуального корня."""
        self.session.execute("cp -r / backup")
        self.assertTrue(self.session.vfs.has_file("/backup/root.txt"))
        self.assertTrue(self.session.vfs.has_file("/backup/docs/nested/deep.txt"))

    def test_previous_commands_still_work(self):
        """Проверить работу команд предыдущего этапа."""
        self.session.execute("cd docs/nested")
        self.assertEqual(self.session.execute("tac deep.txt").output, "two\none")
        self.assertEqual(self.session.execute("ls").output, "deep.txt")
