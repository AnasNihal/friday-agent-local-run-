import unittest

from friday.tools import register_all_tools


class FakeMCP:
    def __init__(self):
        self.tools = []

    def tool(self):
        def decorator(function):
            self.tools.append(function.__name__)
            return function
        return decorator


class MCPTests(unittest.TestCase):
    def test_tool_registration(self):
        server = FakeMCP()
        register_all_tools(server)
        self.assertIn("get_battery_status", server.tools)
        self.assertIn("youtube_search", server.tools)
        self.assertIn("open_file", server.tools)


if __name__ == "__main__":
    unittest.main()
