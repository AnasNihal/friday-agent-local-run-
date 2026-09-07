from pathlib import Path
import tempfile
import unittest

from friday.tools.browser import open_url
from friday.tools.files import list_directory, open_file
from friday.tools.system import get_disk_usage


class ToolTests(unittest.TestCase):
    def test_url_safety(self):
        self.assertIn("only open", open_url("file:///tmp/private"))

    def test_read_only_file_tools(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "hello.txt"
            path.write_text("hello")
            self.assertIn("hello.txt", list_directory(directory))
            self.assertEqual(open_file(str(path)), "hello")

    def test_disk_usage(self):
        self.assertGreater(get_disk_usage("/")["total_bytes"], 0)


if __name__ == "__main__":
    unittest.main()
