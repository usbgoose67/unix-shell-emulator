"""Графический интерфейс эмулятора UNIX-оболочки."""

import getpass
import socket
import tkinter as tk
from tkinter import scrolledtext

from src.config import format_config, parse_config
from src.shell import execute_command
from src.startup import run_startup_script
from src.vfs import format_vfs_info, load_vfs


WINDOW_WIDTH = 760
WINDOW_HEIGHT = 480


class ShellWindow:
    """Графическое окно эмулятора."""

    def __init__(self, root, config):
        """Настроить интерфейс и загрузить конфигурацию."""
        self.root = root
        self.config = config
        self.vfs = None
        username = getpass.getuser()
        hostname = socket.gethostname()
        root.title(f"Эмулятор - [{username}@{hostname}]")
        root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.create_widgets()
        self.show_config()
        self.load_virtual_filesystem()
        root.after(0, self.run_startup)

    def create_widgets(self):
        """Создать историю команд и элементы ввода."""
        self.history = scrolledtext.ScrolledText(
            self.root, state="disabled", wrap="word"
        )
        self.history.pack(fill="both", expand=True, padx=10, pady=10)

        input_frame = tk.Frame(self.root)
        input_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.command_entry = tk.Entry(input_frame)
        self.command_entry.pack(side="left", fill="x", expand=True)
        self.command_entry.bind("<Return>", self.run_command)

        button = tk.Button(
            input_frame, text="Выполнить", command=self.run_command
        )
        button.pack(side="left", padx=(8, 0))
        self.command_entry.focus_set()

    def append_history(self, message):
        """Добавить сообщение в историю команд."""
        self.history.configure(state="normal")
        self.history.insert("end", message + "\n")
        self.history.configure(state="disabled")
        self.history.see("end")

    def show_config(self):
        """Показать все параметры запуска."""
        message = format_config(self.config)
        self.append_history(message)
        self.append_history("")
        print(message)

    def load_virtual_filesystem(self):
        """Загрузить VFS из директории в оперативную память."""
        if not self.config.vfs_path:
            self.append_history("VFS: путь не задан.")
            return

        try:
            self.vfs = load_vfs(self.config.vfs_path)
        except ValueError as error:
            self.append_history(f"Ошибка VFS: {error}")
            return

        message = format_vfs_info(self.vfs)
        self.append_history(message)
        self.append_history("")
        print(message)

    def run_startup(self):
        """Выполнить команды стартового скрипта."""
        if not self.config.startup_path:
            return

        should_exit = run_startup_script(
            self.config.startup_path,
            self.config.prompt,
            self.append_history,
        )
        if should_exit:
            self.root.destroy()

    def run_command(self, event=None):
        """Выполнить введённую пользователем команду."""
        line = self.command_entry.get()
        self.command_entry.delete(0, "end")
        if not line.strip():
            return

        self.append_history(f"{self.config.prompt}{line}")
        result = execute_command(line)
        if result.output:
            self.append_history(result.output)
        if result.should_exit:
            self.root.destroy()


def main():
    """Прочитать конфигурацию и запустить приложение."""
    config = parse_config()
    root = tk.Tk()
    ShellWindow(root, config)
    root.mainloop()


if __name__ == "__main__":
    main()
