"""Автоматические тесты конфигурации эмулятора."""

import unittest

from src.config import format_config, parse_config


class ConfigTests(unittest.TestCase):
    """Проверки параметров командной строки."""

    def test_default_config(self):
        """Проверить значения параметров по умолчанию."""
        config = parse_config([])
        self.assertIsNone(config.vfs_path)
        self.assertEqual(config.prompt, "$ ")
        self.assertIsNone(config.startup_path)

    def test_vfs_parameter(self):
        """Проверить передачу пути VFS."""
        config = parse_config(["--vfs", "example_vfs"])
        self.assertEqual(config.vfs_path, "example_vfs")

    def test_prompt_parameter(self):
        """Проверить пользовательское приглашение."""
        config = parse_config(["--prompt", "student$ "])
        self.assertEqual(config.prompt, "student$ ")

    def test_startup_parameter(self):
        """Проверить путь к стартовому скрипту."""
        config = parse_config(["--startup", "scripts/demo.txt"])
        self.assertEqual(config.startup_path, "scripts/demo.txt")

    def test_all_parameters(self):
        """Проверить одновременную передачу всех параметров."""
        config = parse_config([
            "--vfs", "example_vfs",
            "--prompt", "custom$ ",
            "--startup", "scripts/demo.txt",
        ])
        self.assertEqual(config.vfs_path, "example_vfs")
        self.assertEqual(config.prompt, "custom$ ")
        self.assertEqual(config.startup_path, "scripts/demo.txt")

    def test_debug_output(self):
        """Проверить отладочный вывод параметров."""
        config = parse_config(["--vfs", "example_vfs"])
        output = format_config(config)
        self.assertIn("example_vfs", output)
        self.assertIn("Приглашение:", output)
        self.assertIn("Стартовый скрипт:", output)


if __name__ == "__main__":
    unittest.main()
