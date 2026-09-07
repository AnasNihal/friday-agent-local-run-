"""Safe macOS application controls."""
import platform
import subprocess


def open_application(name: str) -> str:
    if platform.system() != "Darwin":
        return "Application control is currently supported on macOS only."
    result = subprocess.run(["open", "-a", name], capture_output=True, text=True)
    return f"Opened {name}." if result.returncode == 0 else f"I couldn't open {name}: {result.stderr.strip()}"


def close_application(name: str) -> str:
    if platform.system() != "Darwin":
        return "Application control is currently supported on macOS only."
    result = subprocess.run(["osascript", "-e", f'tell application {name!r} to quit'], capture_output=True, text=True)
    return f"Closed {name}." if result.returncode == 0 else f"I couldn't close {name}."


def list_running_applications() -> list[str]:
    if platform.system() != "Darwin":
        return []
    script = 'tell application "System Events" to get name of every process whose background only is false'
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return [item.strip() for item in result.stdout.split(",") if item.strip()]


def register(mcp):
    mcp.tool()(open_application)
    mcp.tool()(close_application)
    mcp.tool()(list_running_applications)
