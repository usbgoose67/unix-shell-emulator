"""Графический интерфейс эмулятора UNIX-оболочки."""

import getpass
import socket
import tkinter as tk
from tkinter import scrolledtext

from src.shell import execute_command


WINDOW_WIDTH = 760
WINDOW_HEIGHT = 480


class ShellWindow:
    """Окно для интерактивного ввода команд эмулятора."""

    def __init__(self, root):
        """Настроить окно и его элементы."""
        self.root = root
        username = getpass.getuser()
        hostname = socket.gethostname()
        root.title(f"Эмулятор - [{username}@{hostname}]")
        root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.create_widgets()

    def create_widgets(self):
        """Создать историю команд, поле ввода и кнопку."""
        self.history = scrolledtext.ScrolledText(
            self.root, state="disabled", wrap="word"
        )
        self.history.pack(fill="both", expand=True, padx=10, pady=10)

        input_frame = tk.Frame(self.root)
        input_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.command_entry = tk.Entry(input_frame)
        self.command_entry.pack(side="left", fill="x", expand=True)
        self.command_entry.bind("<Return>", self.run_command)

        run_button = tk.Button(
            input_frame, text="Выполнить", command=self.run_command
        )
        run_button.pack(side="left", padx=(8, 0))
        self.command_entry.focus_set()

    def append_history(self, message):
        """Добавить строку в историю команд."""
        self.history.configure(state="normal")
        self.history.insert("end", message + "\n")
        self.history.configure(state="disabled")
        self.history.see("end")

    def run_command(self, event=None):
        """Обработать ввод и показать результат выполнения."""
        line = self.command_entry.get()
        self.command_entry.delete(0, "end")
        if not line.strip():
            return

        self.append_history(f"$ {line}")
        result = execute_command(line)
        if result.output:
            self.append_history(result.output)
        if result.should_exit:
            self.root.destroy()


def main():
    """Запустить графический эмулятор."""
    root = tk.Tk()
    ShellWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
