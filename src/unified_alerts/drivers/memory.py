from __future__ import annotations

from unified_alerts.drivers.base import BaseDriver
from unified_alerts.message import AlertMessage


class MemoryDriver(BaseDriver):
    """Stores alerts in-memory outbox list for unit tests and inspection."""

    name = "memory"

    def __init__(self):
        self.outbox: list[AlertMessage] = []

    def send(self, message: AlertMessage) -> bool:
        self.outbox.append(message)
        return True

    def clear(self) -> None:
        self.outbox.clear()

    def test_connection(self) -> tuple[bool, str]:
        return True, "Memory driver ready."
