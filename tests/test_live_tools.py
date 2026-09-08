import platform
import unittest
from unittest.mock import Mock, patch

from friday.tools.applications import open_application
from friday.tools.system import _parse_battery_output


class LiveToolContractTests(unittest.TestCase):
    def test_battery_parser_returns_real_integer(self):
        result = _parse_battery_output(
            "Now drawing from 'Battery Power'\n"
            " -InternalBattery-0 (id=1)\t82%; discharging; 4:12 remaining present: true"
        )
        self.assertTrue(result["success"])
        self.assertIsInstance(result["percentage"], int)
        self.assertGreaterEqual(result["percentage"], 0)
        self.assertLessEqual(result["percentage"], 100)
        self.assertEqual(result["status"], "discharging")

    @patch("friday.tools.applications.platform.system", return_value="Darwin")
    @patch("friday.tools.applications.subprocess.run")
    def test_application_tool_uses_open_a_and_structured_result(self, run, _system):
        run.return_value = Mock(returncode=0, stdout="", stderr="")
        result = open_application("Safari")
        run.assert_called_once_with(["open", "-a", "Safari"], capture_output=True, text=True)
        self.assertEqual(result["success"], True)
        self.assertEqual(result["application"], "Safari")

    @patch("friday.tools.applications.platform.system", return_value="Darwin")
    @patch("friday.tools.applications.subprocess.run")
    def test_application_alias(self, run, _system):
        run.return_value = Mock(returncode=0, stdout="", stderr="")
        open_application("VS Code")
        run.assert_called_once_with(["open", "-a", "Visual Studio Code"], capture_output=True, text=True)


if __name__ == "__main__":
    unittest.main()
