from __future__ import annotations

import logging
import os
from typing import Any

from unified_alerts.drivers.base import BaseDriver
from unified_alerts.drivers.console import ConsoleDriver
from unified_alerts.drivers.memory import MemoryDriver
from unified_alerts.drivers.slack_bot import SlackBotDriver
from unified_alerts.drivers.slack_webhook import SlackWebhookDriver
from unified_alerts.drivers.telegram import TelegramDriver
from unified_alerts.exceptions import ConfigurationException
from unified_alerts.message import AlertMessage

logger = logging.getLogger("unified_alerts")


class AlertManager:
    """Orchestrates configuration and message dispatching to one or more alert drivers."""

    def __init__(self):
        self._drivers: dict[str, BaseDriver] = {}
        self._default_drivers: list[str] = []

    def register(self, name: str, driver: BaseDriver, as_default: bool = False) -> AlertManager:
        self._drivers[name] = driver
        if as_default and name not in self._default_drivers:
            self._default_drivers.append(name)
        return self

    def set_defaults(self, *names: str) -> AlertManager:
        self._default_drivers = [n for n in names if n in self._drivers]
        return self

    def get_driver(self, name: str) -> BaseDriver | None:
        return self._drivers.get(name)

    def configure(self, config: dict[str, Any]) -> AlertManager:
        """
        Configure drivers from a dictionary structure:
        {
            "default": ["slack", "telegram"],
            "drivers": {
                "slack": {
                    "type": "bot",  # or "webhook"
                    "token": "xoxb-...",
                    "channel": "#alerts",
                },
                "telegram": {
                    "token": "123:ABC...",
                    "chat_id": "-100123...",
                },
            }
        }
        """
        drivers_cfg = config.get("drivers", {})
        for name, cfg in drivers_cfg.items():
            driver_type = cfg.get("type", name).lower()

            if driver_type in ("slack_webhook", "webhook"):
                url = cfg.get("url") or cfg.get("webhook_url")
                if url:
                    self.register(name, SlackWebhookDriver(webhook_url=url))
            elif driver_type in ("slack_bot", "slack", "bot"):
                token = cfg.get("token") or cfg.get("bot_token")
                channel = cfg.get("channel") or cfg.get("default_channel", "#alerts")
                if token and channel:
                    self.register(name, SlackBotDriver(token=token, default_channel=channel))
            elif driver_type == "telegram":
                token = cfg.get("token") or cfg.get("bot_token")
                chat_id = cfg.get("chat_id") or cfg.get("default_chat_id")
                if token and chat_id:
                    self.register(name, TelegramDriver(bot_token=token, default_chat_id=chat_id))
            elif driver_type == "console":
                self.register(name, ConsoleDriver(use_color=cfg.get("use_color", True)))
            elif driver_type == "memory":
                self.register(name, MemoryDriver())
            else:
                logger.warning("Unknown alert driver type '%s' for '%s'", driver_type, name)

        default_list = config.get("default", [])
        if isinstance(default_list, str):
            default_list = [default_list]

        if default_list:
            self.set_defaults(*default_list)
        elif self._drivers and not self._default_drivers:
            self._default_drivers = list(self._drivers.keys())

        return self

    @classmethod
    def from_env(cls) -> AlertManager:
        """Load configuration automatically from standard environment variables."""
        manager = cls()

        # Check for mock drivers first
        mode = os.getenv("ALERTS_BACKEND", "").lower()
        if mode == "console":
            manager.register("console", ConsoleDriver(), as_default=True)
            return manager
        if mode == "memory":
            manager.register("memory", MemoryDriver(), as_default=True)
            return manager

        # Slack Webhook
        if webhook_url := os.getenv("SLACK_WEBHOOK_URL"):
            manager.register("slack_webhook", SlackWebhookDriver(webhook_url=webhook_url), as_default=True)

        # Slack Bot
        slack_token = os.getenv("SLACK_BOT_TOKEN")
        slack_channel = os.getenv("SLACK_CHANNEL", "#alerts")
        if slack_token and slack_channel:
            manager.register("slack_bot", SlackBotDriver(token=slack_token, default_channel=slack_channel), as_default=True)

        # Telegram
        tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
        tg_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if tg_token and tg_chat_id:
            manager.register("telegram", TelegramDriver(bot_token=tg_token, default_chat_id=tg_chat_id), as_default=True)

        # If nothing configured, default to console for safe local operation
        if not manager._drivers:
            manager.register("console", ConsoleDriver(), as_default=True)

        return manager

    def send(self, message: AlertMessage, drivers: list[str] | None = None) -> dict[str, bool]:
        target_names = drivers or self._default_drivers
        if not target_names:
            logger.warning("No alert drivers configured or specified. Message not sent: %s", message.title)
            return {}

        results: dict[str, bool] = {}
        for name in target_names:
            driver = self._drivers.get(name)
            if not driver:
                logger.error("Alert driver '%s' not registered.", name)
                results[name] = False
                continue

            try:
                success = driver.send(message)
                results[name] = bool(success)
            except Exception as exc:  # noqa: BLE001 (never crash calling application)
                logger.exception("Driver '%s' raised unexpected exception while sending: %s", name, exc)
                results[name] = False

        return results

    def test(self, driver_name: str | None = None) -> dict[str, tuple[bool, str]]:
        targets = [driver_name] if driver_name else list(self._drivers.keys())
        results = {}
        for name in targets:
            driver = self._drivers.get(name)
            if not driver:
                results[name] = (False, f"Driver '{name}' not found.")
                continue
            try:
                results[name] = driver.test_connection()
            except Exception as exc:  # noqa: BLE001
                results[name] = (False, f"Exception during test: {exc}")
        return results


_default_manager: AlertManager | None = None


def get_default_manager() -> AlertManager:
    global _default_manager
    if _default_manager is None:
        # Check if Django is configured
        try:
            from django.conf import settings  # type: ignore

            if hasattr(settings, "UNIFIED_ALERTS"):
                _default_manager = AlertManager().configure(settings.UNIFIED_ALERTS)
                return _default_manager
        except ImportError:
            pass

        _default_manager = AlertManager.from_env()
    return _default_manager


def set_default_manager(manager: AlertManager) -> None:
    global _default_manager
    _default_manager = manager
