"""Safe macOS application controls."""
import platform
import subprocess
import logging
from friday.config import config


logger = logging.getLogger("friday.tools")

ALIASES = {
    "vs code": "Visual Studio Code",
    "vscode": "Visual Studio Code",
    "code": "Visual Studio Code",
    "chrome": "Google Chrome",
}


def _application_name(name: str) -> str:
    cleaned = " ".join(name.strip().split())
    return ALIASES.get(cleaned.casefold(), cleaned)


def open_application(name: str) -> dict:
    requested = name
    application = _application_name(name)
    if config.debug_tools:
        logger.info("[TOOL CALL] open_application Arguments: %s", {"name": requested})
    if platform.system() != "Darwin":
        result = {"success": False, "message": "Application control is currently supported on macOS only.", "application": requested}
    else:
        try:
            completed = subprocess.run(["open", "-a", application], capture_output=True, text=True, timeout=15)
        except (OSError, subprocess.TimeoutExpired):
            return {"success": False, "message": "Could not start the application opener.", "application": requested}
        if completed.returncode == 0:
            result = {"success": True, "message": f"Opened {application}", "application": application}
        else:
            result = {"success": False, "message": "Application not found", "application": requested, "error": completed.stderr.strip()}
    if config.debug_tools:
        logger.info("[TOOL RESULT] open_application %s", result)
    return result


def close_application(name: str) -> str:
    if platform.system() != "Darwin":
        return "Application control is currently supported on macOS only."
    cleaned = " ".join(name.strip().split())
    if not cleaned:
        return "Please provide an application name."
    try:
        script = "on run argv\n    tell application (item 1 of argv) to quit\nend run"
        result = subprocess.run(["osascript", "-e", script, cleaned], capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        return f"I couldn't close {cleaned}."
    return f"Closed {cleaned}." if result.returncode == 0 else f"I couldn't close {cleaned}."


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
