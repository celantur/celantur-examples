import unittest
import os
from unittest.mock import patch, Mock
import importlib
import queue

client_api = importlib.import_module('cloud-api.cloud-api-v2-client')

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


class TestReadFilesFromFolder(unittest.TestCase):
    def setUp(self):
        self.ROOT_PATH = "mock-test"
        self.SUBDIR_PATH = 'subdirectory'
        self.OUTPUT_PATH= "mock-output-dir"

        # Mock entries
        self.file_ignored = DirEntryMock(path='a.txt')
        self.file_jpg = DirEntryMock(path='b.jpg')
        self.file_JPEG = DirEntryMock(path='c.JPEG')
        self.file_png = DirEntryMock(path='d.png')
        self.subdir = DirEntryMock(path=self.SUBDIR_PATH, is_file=False)
        self.file_JPG = DirEntryMock(path=os.path.join(self.SUBDIR_PATH, 'e.JPG'))
        self.file_jpeg = DirEntryMock(path=os.path.join(self.SUBDIR_PATH, 'f.jpeg'))
        self.file_PNG = DirEntryMock(path=os.path.join(self.SUBDIR_PATH, 'g.PNG'))
        self.root = [self.file_ignored, 
                     self.file_jpg, 
                     self.file_JPEG, 
                     self.file_png, 
                     self.subdir]
        self.subdir_content = [
            self.file_JPG, 
            self.file_jpeg, 
            self.file_PNG
            ]

    def test_extension_normalisation(self):
        results = client_api.normalise_file_extensions(["jpg", "png", ".jpeg"])
        expected = ['.jpg', '.png', '.jpeg']
        self.assertListEqual(expected, results)
        results = client_api.normalise_file_extensions(["jpg", "png", ".jpeg"])
        with self.assertRaises(AttributeError):
            client_api.normalise_file_extensions(["jpg", 'abc'])


    @patch('builtins.open', unittest.mock.mock_open(
        read_data="""{
                "anonymization-method": "blur",
                "face": true,
                "person": true
            }"""
        )
    )
    def test_read_configuration_file(self):
        results = client_api.read_configuration_file('test-file')
        expected = {
            "anonymization-method": "blur",
            "face": True,
            "person": True
        }
        self.assertDictEqual(results, expected)

    @patch('os.scandir', autospec=True)
    def test_read_files_from_folder(self, mock_scandir):

        mock_scandir.side_effect = lambda path: self.subdir_content if path == os.path.join(self.ROOT_PATH, self.SUBDIR_PATH) else self.root

        # Test non-recursive
        result = client_api.get_files_from_(self.ROOT_PATH, '', client_api.EXTENSIONS, recursive=False)
        expected = ['b.jpg', 'c.JPEG', 'd.png']
        self.assertListEqual(expected, list(result))

        # Test recursive
        result = client_api.get_files_from_(self.ROOT_PATH, '', client_api.EXTENSIONS, recursive=True)
        expected = ['b.jpg', 'c.JPEG', 'd.png', 'subdirectory/e.JPG', 'subdirectory/f.jpeg', 'subdirectory/g.PNG']
        self.assertListEqual(expected, list(result))

        # Test recursive without PNG
        result = client_api.get_files_from_(self.ROOT_PATH, '', client_api.EXTENSIONS, recursive=True)
        expected = ['b.jpg', 'c.JPEG', 'd.png', 'subdirectory/e.JPG', 'subdirectory/f.jpeg', 'subdirectory/g.PNG']
        self.assertListEqual(expected, list(result))

        # Test recursive without PNG
        result = client_api.get_files_from_(self.ROOT_PATH, '', ['.jpg', '.jpeg'], recursive=True)
        expected = ['b.jpg', 'c.JPEG', 'subdirectory/e.JPG', 'subdirectory/f.jpeg']
        self.assertListEqual(expected, list(result))

        # Test queueing
        with patch('os.path.exists', autospec=True) as mock_path_exists:
            mock_path_exists.side_effect = lambda path: True if path == os.path.join(self.OUTPUT_PATH, 'c.JPEG') else False

            test_queue = queue.Queue(maxsize=10)
            client_api.get_files_without_overwrite_from_(self.ROOT_PATH, self.OUTPUT_PATH, test_queue, recursive=True, extensions=[".jpg", ".png"])
            result = [] 
            while not test_queue.empty():
                result.append(test_queue.get())
            print(result)
            expected = [('mock-test', 'b.jpg'), ('mock-test', 'd.png'), ('mock-test', 'subdirectory/e.JPG'), ('mock-test', 'subdirectory/g.PNG')]
            self.assertListEqual(expected, result)