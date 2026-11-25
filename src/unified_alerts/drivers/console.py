from __future__ import annotations

import sys
from unified_alerts.drivers.base import BaseDriver
from unified_alerts.enums import AlertLevel
from unified_alerts.message import AlertMessage

# ANSI color codes
COLORS = {
    AlertLevel.INFO: "\033[94m",      # Blue
    AlertLevel.SUCCESS: "\033[92m",   # Green
    AlertLevel.WARNING: "\033[93m",   # Yellow
    AlertLevel.ERROR: "\033[91m",     # Red
    AlertLevel.CRITICAL: "\033[95m",  # Magenta
}
RESET = "\033[0m"
BOLD = "\033[1m"


class ConsoleDriver(BaseDriver):
    """Outputs alerts directly to terminal/stdout. Ideal for local dev and debugging."""

    name = "console"

    def __init__(self, use_color: bool = True):
        self.use_color = use_color and sys.stdout.isatty()

    def send(self, message: AlertMessage) -> bool:
        color = COLORS.get(message.level, "") if self.use_color else ""
        reset = RESET if self.use_color else ""
        bold = BOLD if self.use_color else ""

        bar = f"{color}{'━' * 50}{reset}"
        print(f"\n{bar}")
        print(f"{message.level.emoji} {bold}{message.title}{reset} [{message.level.value.upper()}]")
        if message.text:
            print(f"  {message.text}")

        if message.fields:
            print()
            for f in message.fields:
                print(f"  • {f.label}: {f.value}")

        if message.actions:
            print()
            for a in message.actions:
                print(f"  [Link] {a.label} -> {a.url}")

        if message.channels:
            print(f"  Targets: {', '.join(message.channels)}")

        print(f"{bar}\n")
        return True

    def test_connection(self) -> tuple[bool, str]:
        return True, "Console driver ready."
