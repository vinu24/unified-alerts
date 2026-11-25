"""Alert message data structures and fluent message builder."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

from unified_alerts.enums import AlertLevel


@dataclass(frozen=True)
class AlertField:
    """Key-value metadata attached to an alert."""

    label: str
    value: str
    short: bool = True


@dataclass(frozen=True)
class AlertAction:
    """Action button or link attached to an alert."""

    text: str
    url: str


@dataclass
class AlertMessage:
    """Data representation of an alert with fluent builder capabilities."""

    title: str
    text: str = ""
    level: AlertLevel = AlertLevel.INFO
    fields: list[AlertField] = field(default_factory=list)
    actions: list[AlertAction] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    target_channel: str | None = None
    target_drivers: list[str] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def field(self, label: str, value: Any, short: bool = True) -> AlertMessage:
        """Add a single key-value field to the alert."""
        self.fields.append(AlertField(label=str(label), value=str(value), short=short))
        return self

    def add_fields(self, fields: Mapping[str, Any] | list[tuple[str, Any]]) -> AlertMessage:
        """Add multiple key-value fields at once."""
        items = fields.items() if isinstance(fields, Mapping) else fields
        for k, v in items:
            self.field(k, v)
        return self

    def action(self, text: str, url: str) -> AlertMessage:
        """Add a clickable action button or URL link."""
        self.actions.append(AlertAction(text=str(text), url=str(url)))
        return self

    def channel(self, channel: str) -> AlertMessage:
        """Target a specific channel or recipient (overriding driver default)."""
        self.target_channel = channel
        return self

    def to_driver(self, driver_name: str) -> AlertMessage:
        """Route this specific alert only to the given driver."""
        self.target_drivers = [driver_name]
        return self

    def to_drivers(self, *driver_names: str) -> AlertMessage:
        """Route this specific alert only to the specified drivers."""
        self.target_drivers = list(driver_names)
        return self

    def send(self) -> bool:
        """Dispatch the alert through the global AlertManager."""
        from unified_alerts.manager import get_default_manager

        return get_default_manager().send(self)


class Alert:
    """Static factory for creating fluent AlertMessage instances."""

    @classmethod
    def info(cls, title: str, text: str = "") -> AlertMessage:
        """Create an INFO level alert."""
        return AlertMessage(title=title, text=text, level=AlertLevel.INFO)

    @classmethod
    def success(cls, title: str, text: str = "") -> AlertMessage:
        """Create a SUCCESS level alert."""
        return AlertMessage(title=title, text=text, level=AlertLevel.SUCCESS)

    @classmethod
    def warning(cls, title: str, text: str = "") -> AlertMessage:
        """Create a WARNING level alert."""
        return AlertMessage(title=title, text=text, level=AlertLevel.WARNING)

    @classmethod
    def error(cls, title: str, text: str = "") -> AlertMessage:
        """Create an ERROR level alert."""
        return AlertMessage(title=title, text=text, level=AlertLevel.ERROR)

    @classmethod
    def critical(cls, title: str, text: str = "") -> AlertMessage:
        """Create a CRITICAL level alert."""
        return AlertMessage(title=title, text=text, level=AlertLevel.CRITICAL)

    @classmethod
    def create(cls, title: str, text: str = "", level: AlertLevel = AlertLevel.INFO) -> AlertMessage:
        """Create a custom level alert."""
        return AlertMessage(title=title, text=text, level=level)
