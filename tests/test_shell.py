"""Проверки команд и парсера первого этапа."""

import os
import unittest
from unittest.mock import patch

from src.shell import execute_command, parse_command


class ShellTests(unittest.TestCase):
    """Тесты интерактивных команд эмулятора."""

    def test_ls_without_arguments(self):
        """Команда ls без аргументов возвращает заглушку."""
        self.assertEqual(execute_command("ls").output, "ls: аргументы: []")

    def test_cd_with_arguments(self):
        """Команда cd показывает полученные аргументы."""
        self.assertEqual(
            execute_command("cd documents").output,
            "cd: аргументы: ['documents']",
        )

    def test_environment_variable(self):
        """Переменная окружения раскрывается в аргументе."""
        with patch.dict(os.environ, {"SHELL_TEST_VAR": "example"}):
            self.assertEqual(
                parse_command("ls $SHELL_TEST_VAR"), ["ls", "example"]
            )

    def test_variable_in_braces(self):
        """Переменная в фигурных скобках также раскрывается."""
        with patch.dict(os.environ, {"SHELL_TEST_VAR": "example"}):
            self.assertEqual(
                parse_command("cd ${SHELL_TEST_VAR}"), ["cd", "example"]
            )

    def test_unknown_command(self):
        """Неизвестная команда возвращает ошибку."""
        self.assertIn("неизвестная команда", execute_command("oops").output)

    def test_exit(self):
        """Команда exit запрашивает закрытие окна."""
        self.assertTrue(execute_command("exit").should_exit)

    def test_exit_with_arguments(self):
        """Команда exit с аргументами возвращает ошибку."""
        result = execute_command("exit now")
        self.assertFalse(result.should_exit)
        self.assertIn("не принимает аргументы", result.output)

    def test_empty_input(self):
        """Пустая строка не вызывает ошибку."""
        self.assertEqual(execute_command("   ").output, "")

    def test_unclosed_quotes(self):
        """Незакрытая кавычка возвращает сообщение об ошибке."""
        self.assertIn("Ошибка", execute_command('ls "oops').output)


if __name__ == "__main__":
    unittest.main()
