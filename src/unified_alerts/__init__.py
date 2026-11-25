"""
unified-alerts: Clean, unified alerts for Slack and Telegram with zero dependencies.
"""

from unified_alerts.enums import AlertLevel
from unified_alerts.manager import AlertManager, get_default_manager, set_default_manager
from unified_alerts.message import Alert, AlertAction, AlertField, AlertMessage


def send_alert(title: str, text: str | None = None, level: AlertLevel = AlertLevel.INFO, **fields) -> dict[str, bool]:
    """Quick one-line alert sender."""
    msg = AlertMessage(title=title, text=text, level=level)
    for k, v in fields.items():
        msg.field(k, v)
    return msg.send()


__all__ = [
    "Alert",
    "AlertAction",
    "AlertField",
    "AlertLevel",
    "AlertManager",
    "AlertMessage",
    "get_default_manager",
    "send_alert",
    "set_default_manager",
]

__version__ = "0.1.0"
