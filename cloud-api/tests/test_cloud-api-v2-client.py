import unittest
import os
from unittest.mock import patch
import importlib.util
import queue
from pathlib import Path

_CLIENT_PATH = Path(__file__).resolve().parents[1] / 'cloud-api-v2-client.py'
_spec = importlib.util.spec_from_file_location('cloud_api_v2_client', _CLIENT_PATH)
client_api = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(client_api)


class DirEntryMock:
    def __init__(self, path: str, is_file: bool = True):
        self._is_file = is_file
        self.path = path

    def is_file(self):
        return self._is_file

    def is_dir(self):
        return not self._is_file

    @property
    def name(self):
        return os.path.basename(self.path)


class FakeInputFolderTestCase(unittest.TestCase):
    """Shared mock directory tree with images, videos, and an ignored file."""

    def setUp(self):
        self.ROOT_PATH = "mock-test"
        self.SUBDIR_PATH = 'subdirectory'
        self.OUTPUT_PATH = "mock-output-dir"

        self.file_ignored = DirEntryMock(path='a.txt')
        self.file_jpg = DirEntryMock(path='b.jpg')
        self.file_JPEG = DirEntryMock(path='c.JPEG')
        self.file_png = DirEntryMock(path='d.png')
        self.file_mp4 = DirEntryMock(path='h.mp4')
        self.file_AVI = DirEntryMock(path='i.AVI')
        self.subdir = DirEntryMock(path=self.SUBDIR_PATH, is_file=False)
        self.file_JPG = DirEntryMock(path=os.path.join(self.SUBDIR_PATH, 'e.JPG'))
        self.file_jpeg = DirEntryMock(path=os.path.join(self.SUBDIR_PATH, 'f.jpeg'))
        self.file_PNG = DirEntryMock(path=os.path.join(self.SUBDIR_PATH, 'g.PNG'))
        self.file_mkv = DirEntryMock(path=os.path.join(self.SUBDIR_PATH, 'j.mkv'))
        self.file_MOV = DirEntryMock(path=os.path.join(self.SUBDIR_PATH, 'k.MOV'))
        self.root = [
            self.file_ignored,
            self.file_jpg,
            self.file_JPEG,
            self.file_png,
            self.file_mp4,
            self.file_AVI,
            self.subdir,
        ]
        self.subdir_content = [
            self.file_JPG,
            self.file_jpeg,
            self.file_PNG,
            self.file_mkv,
            self.file_MOV,
        ]

    def mock_scandir(self):
        return patch(
            'os.scandir',
            autospec=True,
            side_effect=lambda path: (
                self.subdir_content
                if path == os.path.join(self.ROOT_PATH, self.SUBDIR_PATH)
                else self.root
            ),
        )

    def list_files(self, extensions, recursive):
        with self.mock_scandir():
            return list(
                client_api.get_files_from_(self.ROOT_PATH, '', extensions, recursive=recursive)
            )


class TestNormaliseFileExtensions(unittest.TestCase):
    def test_normalises_image_extensions(self):
        results = client_api.normalise_file_extensions(["jpg", "png", ".jpeg"])
        self.assertListEqual(['.jpg', '.png', '.jpeg'], results)

    def test_normalises_video_extensions(self):
        results = client_api.normalise_file_extensions(["mp4", ".avi", "mkv", "MOV"])
        self.assertListEqual(['.mp4', '.avi', '.mkv', '.mov'], results)

    def test_defaults_when_unspecified(self):
        self.assertListEqual(
            client_api.DEFAULT_EXTENSIONS,
            client_api.normalise_file_extensions(None),
        )
        self.assertListEqual(
            client_api.DEFAULT_EXTENSIONS,
            client_api.normalise_file_extensions([]),
        )

    def test_rejects_unsupported_extension(self):
        with self.assertRaises(AttributeError):
            client_api.normalise_file_extensions(["jpg", 'abc'])


class TestReadConfigurationFile(unittest.TestCase):
    @patch('builtins.open', unittest.mock.mock_open(
        read_data="""{
                "anonymization-method": "blur",
                "face": true,
                "person": true
            }"""
        )
    )
    def test_reads_json_configuration(self):
        results = client_api.read_configuration_file('test-file')
        expected = {
            "anonymization-method": "blur",
            "face": True,
            "person": True
        }
        self.assertDictEqual(results, expected)


class TestReadFilesFromFolder(FakeInputFolderTestCase):
    def test_non_recursive_lists_only_root_images(self):
        result = self.list_files(client_api.DEFAULT_EXTENSIONS, recursive=False)
        self.assertListEqual(['b.jpg', 'c.JPEG', 'd.png'], result)

    def test_recursive_lists_images_and_skips_videos(self):
        result = self.list_files(client_api.DEFAULT_EXTENSIONS, recursive=True)
        self.assertListEqual(
            [
                'b.jpg',
                'c.JPEG',
                'd.png',
                'subdirectory/e.JPG',
                'subdirectory/f.jpeg',
                'subdirectory/g.PNG',
            ],
            result,
        )

    def test_recursive_filters_by_requested_extensions(self):
        result = self.list_files(['.jpg', '.jpeg'], recursive=True)
        self.assertListEqual(
            ['b.jpg', 'c.JPEG', 'subdirectory/e.JPG', 'subdirectory/f.jpeg'],
            result,
        )

    def test_supported_extensions_include_video_files(self):
        result = self.list_files(client_api.SUPPORTED_EXTENSIONS, recursive=True)
        self.assertListEqual(
            [
                'b.jpg',
                'c.JPEG',
                'd.png',
                'h.mp4',
                'i.AVI',
                'subdirectory/e.JPG',
                'subdirectory/f.jpeg',
                'subdirectory/g.PNG',
                'subdirectory/j.mkv',
                'subdirectory/k.MOV',
            ],
            result,
        )

    def test_mp4_file_type_lists_only_mp4(self):
        result = self.list_files(['.mp4'], recursive=True)
        self.assertListEqual(['h.mp4'], result)


class TestQueueWithoutOverwrite(FakeInputFolderTestCase):
    def test_skips_files_that_already_exist_in_output(self):
        existing = os.path.join(self.OUTPUT_PATH, 'b.jpg')
        with self.mock_scandir(), patch('os.path.exists', autospec=True) as mock_path_exists:
            mock_path_exists.side_effect = lambda path: path == existing
            test_queue = queue.Queue(maxsize=10)
            client_api.get_files_without_overwrite_from_(
                self.ROOT_PATH,
                self.OUTPUT_PATH,
                test_queue,
                recursive=True,
                extensions=[".jpg", ".png"],
            )
            result = []
            while not test_queue.empty():
                result.append(test_queue.get())

        self.assertListEqual(
            [
                ('mock-test', 'd.png'),
                ('mock-test', 'subdirectory/e.JPG'),
                ('mock-test', 'subdirectory/g.PNG'),
            ],
            result,
        )
