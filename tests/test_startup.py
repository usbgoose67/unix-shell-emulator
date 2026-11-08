"""Автоматические тесты стартовых скриптов."""

import tempfile
import unittest
from pathlib import Path

from src.startup import run_startup_script


class StartupTests(unittest.TestCase):
    """Проверки последовательного выполнения команд."""

    def run_script(self, content):
        """Создать временный скрипт и собрать его вывод."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "startup.txt"
            path.write_text(content, encoding="utf-8")
            messages = []
            should_exit = run_startup_script(
                path, "test$ ", messages.append
            )
        return messages, should_exit

    def test_commands_in_order(self):
        """Проверить последовательность выполнения команд."""
        messages, _ = self.run_script("ls\ncd documents\n")
        self.assertEqual(messages[0], "test$ ls")
        self.assertEqual(messages[2], "test$ cd documents")

    def test_skip_errors(self):
        """Проверить продолжение после ошибочной команды."""
        messages, _ = self.run_script("unknown\nls\n")
        self.assertIn("test$ ls", messages)
        self.assertIn("Ошибка", messages[1])

    def test_skip_empty_lines(self):
        """Проверить пропуск пустых строк."""
        messages, _ = self.run_script("\nls\n\n")
        self.assertEqual(len(messages), 2)

    def test_exit_stops_script(self):
        """Проверить завершение скрипта командой exit."""
        messages, should_exit = self.run_script("exit\nls\n")
        self.assertTrue(should_exit)
        self.assertNotIn("test$ ls", messages)

    def test_missing_file(self):
        """Проверить сообщение об отсутствующем файле."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.txt"
            messages = []
            result = run_startup_script(
                path, "$ ", messages.append
            )
        self.assertFalse(result)
        self.assertIn("Ошибка загрузки", messages[0])

    def test_invalid_exit_continues(self):
        """Проверить продолжение после ошибочного exit."""
        messages, should_exit = self.run_script("exit now\nls\n")
        self.assertFalse(should_exit)
        self.assertIn("test$ ls", messages)


if __name__ == "__main__":
    unittest.main()
