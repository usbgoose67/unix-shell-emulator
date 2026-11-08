"""Автоматические тесты виртуальной файловой системы."""

import tempfile
import unittest
from pathlib import Path

from src.vfs import format_vfs_info, load_vfs


class VfsTests(unittest.TestCase):
    """Проверки загрузки VFS и работы с данными в памяти."""

    def setUp(self):
        """Создать временную исходную директорию."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)

    def create_file(self, relative_path, content):
        """Создать тестовый файл в исходной директории."""
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def test_minimal_vfs(self):
        """Проверить загрузку минимальной VFS."""
        self.create_file("readme.txt", b"hello")
        vfs = load_vfs(self.root)
        self.assertEqual(vfs.file_count, 1)
        self.assertEqual(vfs.directory_count, 1)

    def test_multiple_files(self):
        """Проверить загрузку нескольких файлов."""
        self.create_file("first.txt", b"one")
        self.create_file("second.txt", b"two")
        vfs = load_vfs(self.root)
        self.assertEqual(vfs.file_count, 2)

    def test_deep_structure(self):
        """Проверить вложенность из трёх каталогов."""
        self.create_file("a/b/c/data.txt", b"deep")
        vfs = load_vfs(self.root)
        self.assertTrue(vfs.has_directory("/a/b/c"))
        self.assertTrue(vfs.has_file("/a/b/c/data.txt"))
        self.assertEqual(vfs.directory_count, 4)

    def test_file_content(self):
        """Проверить содержимое файла в памяти."""
        self.create_file("data.txt", b"original")
        vfs = load_vfs(self.root)
        self.assertEqual(vfs.read_file("/data.txt"), b"original")

    def test_source_is_unchanged(self):
        """Проверить отсутствие изменений исходного файла."""
        source = self.create_file("data.txt", b"original")
        vfs = load_vfs(self.root)
        vfs.files["/data.txt"] = b"modified"
        self.assertEqual(source.read_bytes(), b"original")

    def test_empty_directory(self):
        """Проверить сохранение пустого каталога."""
        (self.root / "empty").mkdir()
        vfs = load_vfs(self.root)
        self.assertTrue(vfs.has_directory("/empty"))
        self.assertEqual(vfs.file_count, 0)

    def test_missing_directory(self):
        """Проверить ошибку отсутствующей директории."""
        missing = self.root / "missing"
        with self.assertRaises(ValueError):
            load_vfs(missing)

    def test_file_instead_of_directory(self):
        """Проверить ошибку при передаче пути к файлу."""
        path = self.create_file("data.txt", b"hello")
        with self.assertRaises(ValueError):
            load_vfs(path)

    def test_binary_content(self):
        """Проверить загрузку бинарного содержимого."""
        content = bytes([0, 1, 2, 255])
        self.create_file("data.bin", content)
        vfs = load_vfs(self.root)
        self.assertEqual(vfs.read_file("/data.bin"), content)

    def test_debug_information(self):
        """Проверить отображение количества объектов."""
        self.create_file("folder/data.txt", b"hello")
        vfs = load_vfs(self.root)
        message = format_vfs_info(vfs)
        self.assertIn("Каталогов: 2", message)
        self.assertIn("Файлов: 1", message)


if __name__ == "__main__":
    unittest.main()
