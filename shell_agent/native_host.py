import os
import sys
import platform
import subprocess
import shutil
from typing import Dict, Any, Optional

class NativeHostAutomation:
    """
    Phase 3: Native OS Automation Hooks.
    Cross-platform HAL driver for controlling host OS capabilities
    on Windows, macOS, and Linux.
    """

    def __init__(self):
        self.os_type = platform.system() # 'Windows', 'Darwin', 'Linux'
        print(f"[HostAutomation] Native OS driver active for platform: {self.os_type}")

    def launch_application(self, app_name: str) -> Dict[str, Any]:
        """Launches a desktop application on the host operating system."""
        try:
            if self.os_type == "Windows":
                # Safe application launch mapping
                allowed_apps = {
                    "notepad": "notepad.exe",
                    "calculator": "calc.exe",
                    "calc": "calc.exe",
                    "explorer": "explorer.exe",
                    "browser": "start"
                }
                cmd = allowed_apps.get(app_name.lower(), app_name)
                subprocess.Popen(cmd, shell=True)
                return {"status": "SUCCESS", "message": f"Launched '{app_name}' on Windows."}

            elif self.os_type == "Darwin": # macOS
                subprocess.Popen(["open", "-a", app_name])
                return {"status": "SUCCESS", "message": f"Launched '{app_name}' on macOS."}

            else: # Linux
                subprocess.Popen([app_name], shell=True)
                return {"status": "SUCCESS", "message": f"Launched '{app_name}' on Linux."}

        except Exception as e:
            return {"status": "ERROR", "message": f"Failed to launch app: {str(e)}"}

    def show_desktop_notification(self, title: str, message: str) -> bool:
        """Dispatches native desktop notifications using OS-specific notification bus."""
        try:
            if self.os_type == "Windows":
                # PowerShell balloon notification without extra dependency
                ps_script = f"""
                [reflection.assembly]::loadwithpartialname('System.Windows.Forms') | Out-Null
                $notify = new-object system.windows.forms.notifyicon
                $notify.icon = [system.drawing.systemicons]::Information
                $notify.visible = $true
                $notify.showballoontip(3000, '{title}', '{message}', [system.windows.forms.tooltipicon]::Info)
                """
                subprocess.run(["powershell", "-Command", ps_script], check=False, timeout=5, creationflags=0x08000000 if os.name == 'nt' else 0)
                return True

            elif self.os_type == "Darwin":
                osascript = f'display notification "{message}" with title "{title}"'
                subprocess.run(["osascript", "-e", osascript], check=False, timeout=5)
                return True

            else: # Linux
                if shutil.which("notify-send"):
                    subprocess.run(["notify-send", title, message], check=False, timeout=5)
                    return True
        except Exception:
            pass
        return False

    def get_system_telemetry(self) -> Dict[str, Any]:
        """Queries CPU, memory, and platform diagnostic telemetry."""
        telemetry = {
            "platform": self.os_type,
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
            "hostname": platform.node()
        }
        try:
            import psutil # type: ignore
            telemetry["cpu_percent"] = psutil.cpu_percent(interval=0.1)
            telemetry["memory_percent"] = psutil.virtual_memory().percent
            battery = psutil.sensors_battery()
            telemetry["battery"] = f"{battery.percent}%" if battery else "N/A (AC Power)"
        except ImportError:
            telemetry["cpu_percent"] = "N/A"
            telemetry["memory_percent"] = "N/A"
            telemetry["battery"] = "AC Power"

        return telemetry

    def execute_action(self, action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Dispatches an abstract host automation action."""
        params = params or {}
        act = action.lower()

        if act == "launch_app":
            app = params.get("app", "notepad")
            return self.launch_application(app)
        elif act == "notify":
            title = params.get("title", "AOS Notification")
            msg = params.get("message", "System Alert")
            success = self.show_desktop_notification(title, msg)
            return {"status": "SUCCESS" if success else "FALLBACK", "notified": success}
        elif act in ["stats", "telemetry", "get_stats"]:
            return {"status": "SUCCESS", "telemetry": self.get_system_telemetry()}
        else:
            return {"status": "ERROR", "message": f"Unsupported host action: {action}"}
