"""
System tools — time, environment info, shell commands, etc.
"""

import datetime
import platform
import shutil
import subprocess


def get_battery_status() -> dict | str:
    if platform.system() != "Darwin":
        return "Battery status is currently supported on macOS only."
    result = subprocess.run(["pmset", "-g", "batt"], capture_output=True, text=True)
    line = result.stdout.splitlines()[-1] if result.stdout.splitlines() else ""
    return {"raw": line, "charging": "AC Power" in result.stdout}


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
