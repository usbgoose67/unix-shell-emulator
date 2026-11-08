"""Тесты команд и парсера эмулятора."""

import os
import unittest
from unittest.mock import patch

from src.shell import execute_command, parse_command


class ShellTests(unittest.TestCase):
    """Проверки команд первого и второго этапов."""

    def test_ls_without_arguments(self):
        """Проверить ls без аргументов."""
        self.assertEqual(execute_command("ls").output, "ls: аргументы: []")

    def test_cd_with_arguments(self):
        """Проверить cd с аргументом."""
        self.assertEqual(
            execute_command("cd documents").output,
            "cd: аргументы: ['documents']",
        )

    def test_environment_variable(self):
        """Проверить раскрытие переменной окружения."""
        with patch.dict(os.environ, {"SHELL_TEST_VAR": "example"}):
            self.assertEqual(
                parse_command("ls $SHELL_TEST_VAR"), ["ls", "example"]
            )

    def test_variable_in_braces(self):
        """Проверить переменную в фигурных скобках."""
        with patch.dict(os.environ, {"SHELL_TEST_VAR": "example"}):
            self.assertEqual(
                parse_command("cd ${SHELL_TEST_VAR}"), ["cd", "example"]
            )

    def test_unknown_command(self):
        """Проверить сообщение о неизвестной команде."""
        result = execute_command("oops")
        self.assertIn("неизвестная команда", result.output)

    def test_exit(self):
        """Проверить корректное завершение работы."""
        self.assertTrue(execute_command("exit").should_exit)

    def test_exit_with_arguments(self):
        """Проверить ошибку аргументов exit."""
        result = execute_command("exit now")
        self.assertFalse(result.should_exit)
        self.assertIn("не принимает аргументы", result.output)

    def test_empty_input(self):
        """Проверить обработку пустого ввода."""
        self.assertEqual(execute_command("   ").output, "")

    def test_unclosed_quotes(self):
        """Проверить обработку незакрытых кавычек."""
        self.assertIn("Ошибка", execute_command('ls "oops').output)

    def test_error_flag(self):
        """Проверить признак ошибки выполнения."""
        self.assertTrue(execute_command("unknown").is_error)
        self.assertFalse(execute_command("ls").is_error)


if __name__ == "__main__":
    unittest.main()
