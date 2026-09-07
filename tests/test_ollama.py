import unittest
from unittest.mock import Mock, patch

from friday.ollama import list_models


class OllamaTests(unittest.TestCase):
    @patch("friday.ollama.httpx.get")
    def test_model_listing(self, get):
        response = Mock()
        response.json.return_value = {"models": [{"name": "qwen2.5:7b"}]}
        get.return_value = response
        self.assertEqual(list_models(), ["qwen2.5:7b"])


if __name__ == "__main__":
    unittest.main()
