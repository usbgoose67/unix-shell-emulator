"""Загрузка и выполнение стартовых скриптов."""

from pathlib import Path

from src.shell import execute_command


def read_startup_script(path):
    """Прочитать команды из текстового файла UTF-8."""
    return Path(path).read_text(encoding="utf-8-sig").splitlines()


def run_startup_script(path, prompt, show_output, executor=None):
    """Выполнить команды, продолжая работу после ошибок."""
    if executor is None:
        executor = execute_command

    try:
        lines = read_startup_script(path)
    except (OSError, UnicodeError) as error:
        show_output(f"Ошибка загрузки скрипта: {error}")
        return False

    for line in lines:
        if not line.strip():
            continue

        show_output(f"{prompt}{line}")
        result = executor(line)

        if result.output:
            show_output(result.output)

        if result.should_exit:
            return True

    return False
