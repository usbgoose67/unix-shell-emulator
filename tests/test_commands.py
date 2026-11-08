"""Тесты основных команд UNIX-эмулятора."""

import getpass
import tempfile
import unittest
from pathlib import Path

from src.shell import ShellSession
from src.startup import run_startup_script
from src.vfs import load_vfs


class CommandTests(unittest.TestCase):
    """Проверки команд с виртуальной файловой системой."""

    def setUp(self):
        """Создать тестовую VFS и командную сессию."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        (self.root / "docs" / "nested").mkdir(parents=True)
        (self.root / "hello.txt").write_text(
            "first\nsecond\nthird\n", encoding="utf-8"
        )
        (self.root / "docs" / "note.txt").write_text(
            "one\ntwo\n", encoding="utf-8"
        )
        self.session = ShellSession(load_vfs(self.root))

    def test_ls_root(self):
        """Проверить содержимое корневого каталога."""
        result = self.session.execute("ls")
        self.assertEqual(result.output, "docs/\nhello.txt")

    def test_ls_directory(self):
        """Проверить вывод содержимого указанного каталога."""
        result = self.session.execute("ls docs")
        self.assertEqual(result.output, "nested/\nnote.txt")

    def test_ls_file(self):
        """Проверить вывод имени отдельного файла."""
        result = self.session.execute("ls hello.txt")
        self.assertEqual(result.output, "hello.txt")

    def test_ls_missing_path(self):
        """Проверить ошибку отсутствующего пути."""
        result = self.session.execute("ls missing")
        self.assertTrue(result.is_error)

    def test_cd_directory(self):
        """Проверить переход в каталог."""
        self.session.execute("cd docs")
        self.assertEqual(self.session.cwd, "/docs")

    def test_cd_parent(self):
        """Проверить переход в родительский каталог."""
        self.session.execute("cd docs/nested")
        self.session.execute("cd ..")
        self.assertEqual(self.session.cwd, "/docs")

    def test_cd_root(self):
        """Проверить переход в корень VFS."""
        self.session.execute("cd docs")
        self.session.execute("cd /")
        self.assertEqual(self.session.cwd, "/")

    def test_cd_missing_directory(self):
        """Проверить сохранение пути после ошибки cd."""
        result = self.session.execute("cd missing")
        self.assertTrue(result.is_error)
        self.assertEqual(self.session.cwd, "/")

    def test_ls_after_cd(self):
        """Проверить ls после смены каталога."""
        self.session.execute("cd docs")
        result = self.session.execute("ls")
        self.assertEqual(result.output, "nested/\nnote.txt")

    def test_tac_file(self):
        """Проверить обратный порядок строк файла."""
        result = self.session.execute("tac hello.txt")
        self.assertEqual(result.output, "third\nsecond\nfirst")

    def test_tac_relative_path(self):
        """Проверить tac после смены каталога."""
        self.session.execute("cd docs")
        result = self.session.execute("tac note.txt")
        self.assertEqual(result.output, "two\none")

    def test_tac_missing_file(self):
        """Проверить ошибку отсутствующего файла."""
        result = self.session.execute("tac missing.txt")
        self.assertTrue(result.is_error)

    def test_whoami(self):
        """Проверить имя пользователя операционной системы."""
        result = self.session.execute("whoami")
        self.assertEqual(result.output, getpass.getuser())

    def test_whoami_arguments(self):
        """Проверить запрет аргументов whoami."""
        result = self.session.execute("whoami extra")
        self.assertTrue(result.is_error)

    def test_invalid_argument_counts(self):
        """Проверить неправильное число аргументов."""
        commands = ("ls a b", "cd a b", "tac", "tac a b")
        for command in commands:
            with self.subTest(command=command):
                self.assertTrue(self.session.execute(command).is_error)

    def test_exit(self):
        """Проверить завершение командной сессии."""
        result = self.session.execute("exit")
        self.assertTrue(result.should_exit)

    def test_startup_keeps_directory(self):
        """Проверить сохранение каталога после скрипта."""
        script = self.root / "commands.txt"
        script.write_text("cd docs\nls\n", encoding="utf-8")
        messages = []
        run_startup_script(
            script, "$ ", messages.append, self.session.execute
        )
        self.assertEqual(self.session.cwd, "/docs")
        self.assertIn("nested/\nnote.txt", messages)

    def test_source_file_is_unchanged(self):
        """Проверить сохранность исходного файла после tac."""
        path = self.root / "hello.txt"
        original = path.read_bytes()
        self.session.execute("tac hello.txt")
        self.assertEqual(path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
