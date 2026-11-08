"""Настройки запуска графического эмулятора."""

import argparse
from dataclasses import dataclass


DEFAULT_PROMPT = "$ "


@dataclass(frozen=True)
class EmulatorConfig:
    """Параметры конфигурации эмулятора."""

    vfs_path: str | None
    prompt: str
    startup_path: str | None


def parse_config(arguments=None):
    """Получить параметры из командной строки."""
    parser = argparse.ArgumentParser(
        description="Графический эмулятор UNIX-оболочки"
    )
    parser.add_argument(
        "--vfs",
        dest="vfs_path",
        default=None,
        help="Путь к физическому расположению VFS",
    )
    parser.add_argument(
        "--prompt",
        default=DEFAULT_PROMPT,
        help="Пользовательское приглашение к вводу",
    )
    parser.add_argument(
        "--startup",
        dest="startup_path",
        default=None,
        help="Путь к стартовому скрипту",
    )
    namespace = parser.parse_args(arguments)
    return EmulatorConfig(
        vfs_path=namespace.vfs_path,
        prompt=namespace.prompt,
        startup_path=namespace.startup_path,
    )


def format_config(config):
    """Подготовить отладочный вывод всех параметров."""
    vfs_path = config.vfs_path or "не задан"
    startup_path = config.startup_path or "не задан"
    return (
        "Конфигурация эмулятора:\n"
        f"VFS: {vfs_path}\n"
        f"Приглашение: {config.prompt}\n"
        f"Стартовый скрипт: {startup_path}"
    )
