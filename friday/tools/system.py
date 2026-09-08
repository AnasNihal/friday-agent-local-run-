"""
System tools — time, environment info, shell commands, etc.
"""

import datetime
import platform
import shutil
import subprocess
import re
import logging
from friday.config import config


logger = logging.getLogger("friday.tools")


def _parse_battery_output(output: str) -> dict:
    match = re.search(r"(?P<percentage>\d{1,3})%;\s*(?P<status>[A-Za-z -]+);", output)
    if not match:
        return {"success": False, "message": "Could not parse battery status from pmset output", "raw": output.strip()}
    return {
        "success": True,
        "percentage": int(match.group("percentage")),
        "status": match.group("status").strip().lower(),
    }


def get_battery_status() -> dict:
    if config.debug_tools:
        logger.info("[TOOL CALL] get_battery_status Arguments: {}")
    if platform.system() != "Darwin":
        result = {"success": False, "message": "Battery status is currently supported on macOS only."}
    else:
        completed = subprocess.run(["pmset", "-g", "batt"], capture_output=True, text=True)
        output = completed.stdout
        result = _parse_battery_output(output) if completed.returncode == 0 else {
            "success": False,
            "message": "Could not read battery status from pmset",
            "raw": output.strip(),
        }
    if config.debug_tools:
        logger.info("[TOOL RESULT] get_battery_status %s", result)
    return result


def get_cpu_usage() -> str:
    if platform.system() == "Darwin":
        result = subprocess.run(["top", "-l", "1", "-n", "0"], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if "CPU usage" in line:
                return line.strip()
    return "CPU usage unavailable on this platform."


def get_memory_usage() -> str:
    if platform.system() == "Darwin":
        result = subprocess.run(["vm_stat"], capture_output=True, text=True)
        return result.stdout[:1000]
    return "Memory usage unavailable on this platform."


def get_disk_usage(path: str = "/") -> dict:
    usage = shutil.disk_usage(path)
    return {"path": path, "total_bytes": usage.total, "used_bytes": usage.used, "free_bytes": usage.free}


def get_current_time() -> str:
    return datetime.datetime.now().astimezone().strftime("%A, %B %-d %Y at %-I:%M %p %Z")


def register(mcp):

    @mcp.tool()
    def get_system_info() -> dict:
        """Return basic information about the host system."""
        return {
            "os": platform.system(),
            "os_version": platform.version(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
        }

    mcp.tool()(get_battery_status)
    mcp.tool()(get_current_time)
    mcp.tool()(get_cpu_usage)
    mcp.tool()(get_memory_usage)
    mcp.tool()(get_disk_usage)
