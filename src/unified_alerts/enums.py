"""Alert level enumerations and associated styling attributes."""

from enum import Enum


class AlertLevel(str, Enum):
    """Severity levels for alerts."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

    @property
    def emoji(self) -> str:
        """Default emoji representation for each alert level."""
        mapping = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.SUCCESS: "✅",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.ERROR: "🚨",
            AlertLevel.CRITICAL: "🔥",
        }
        return mapping[self]

    @property
    def color_hex(self) -> str:
        """Hex color code for Slack attachments / borders."""
        mapping = {
            AlertLevel.INFO: "#2563EB",  # Blue
            AlertLevel.SUCCESS: "#16A34A",  # Green
            AlertLevel.WARNING: "#EAB308",  # Amber / Yellow
            AlertLevel.ERROR: "#DC2626",  # Red
            AlertLevel.CRITICAL: "#7F1D1D",  # Dark Red
        }
        return mapping[self]

    @property
    def title_prefix(self) -> str:
        """Upper-cased title prefix."""
        return self.value.upper()
