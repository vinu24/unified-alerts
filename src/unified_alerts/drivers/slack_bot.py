"""Slack Bot Token (chat.postMessage) alert driver."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any

from unified_alerts.drivers.base import BaseDriver
from unified_alerts.drivers.slack_webhook import SlackWebhookDriver, escape_mrkdwn
from unified_alerts.exceptions import ConfigurationError
from unified_alerts.message import AlertMessage

logger = logging.getLogger("unified_alerts.slack_bot")

SLACK_POST_MESSAGE_URL = "https://slack.com/api/chat.postMessage"
SLACK_AUTH_TEST_URL = "https://slack.com/api/auth.test"


class SlackBotDriver(BaseDriver):
    """Sends alert notifications through a Slack App Bot Token to configurable channels."""

    name = "slack_bot"

    def __init__(
        self,
        bot_token: str | None = None,
        default_channel: str = "#alerts",
        timeout: float = 10.0,
        token: str | None = None,
        **kwargs: Any,
    ) -> None:
        raw_token = (bot_token or token or "").strip()
        super().__init__(
            bot_token=raw_token,
            default_channel=default_channel,
            timeout=timeout,
            **kwargs,
        )
        if not raw_token or not raw_token.startswith("xoxb-"):
            raise ConfigurationError("SlackBotDriver requires a valid bot token starting with 'xoxb-'.")
        if not default_channel:
            raise ConfigurationError("SlackBotDriver requires a non-empty 'default_channel'")

        self.bot_token = raw_token
        self.default_channel = default_channel.lstrip("#")
        self.timeout = float(timeout)

    def _format_target_channel(self, channel: str | None) -> str:
        raw = channel or self.default_channel
        # Channel IDs (C123...) or channel names
        return raw.strip().lstrip("#")

    def send(self, message: AlertMessage) -> bool:
        """Send message using Slack's chat.postMessage API."""
        target_channel = self._format_target_channel(message.target_channel)

        # Build payload using same structure as webhook driver
        webhook_helper = SlackWebhookDriver(webhook_url="https://dummy.example.com")
        payload = webhook_helper._build_payload(message)
        payload["channel"] = target_channel

        status, data = self._http_post(
            SLACK_POST_MESSAGE_URL,
            payload,
            headers={"Authorization": f"Bearer {self.bot_token}"},
            timeout=self.timeout,
        )

        if 200 <= status < 300:
            if isinstance(data, dict):
                if data.get("ok"):
                    return True
                error_code = data.get("error", "unknown_error")
                hint = self._diagnose_slack_error(error_code, target_channel)
                logger.error("Slack bot delivery to #%s failed: %s (%s)", target_channel, error_code, hint)
                return False
            return data == "ok"

        logger.error("Slack API HTTP error %d: %s", status, data)
        return False

    def test_connection(self) -> dict[str, Any]:
        """Verify the bot token using Slack's auth.test API."""
        req = urllib.request.Request(
            SLACK_AUTH_TEST_URL,
            headers={"Authorization": f"Bearer {self.bot_token}"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8") or "{}")

            if data.get("ok"):
                return {
                    "ok": True,
                    "driver": self.name,
                    "status": "connected",
                    "bot_id": data.get("bot_id"),
                    "user": data.get("user"),
                    "team": data.get("team"),
                    "default_channel": f"#{self.default_channel}",
                }

            error = data.get("error", "auth_failed")
            return {
                "ok": False,
                "driver": self.name,
                "status": "auth_failed",
                "error": error,
                "hint": self._diagnose_slack_error(error, self.default_channel),
            }
        except Exception as exc:
            return {
                "ok": False,
                "driver": self.name,
                "status": "connection_error",
                "error": str(exc),
            }

    @staticmethod
    def _diagnose_slack_error(code: str, channel: str) -> str:
        """Provide actionable guidance for common Slack API errors."""
        hints = {
            "channel_not_found": f"Channel #{channel} does not exist or the bot was not invited.",
            "not_in_channel": f"Bot is not in #{channel}. In Slack, run '/invite @your_bot' in that channel.",
            "invalid_auth": "Bot token is invalid. Make sure it begins with 'xoxb-'.",
            "missing_scope": "Bot token is missing required OAuth scope: 'chat:write'.",
            "account_inactive": "The Slack bot account has been disabled.",
            "rate_limited": "Slack API rate limit exceeded.",
        }
        return hints.get(code, "Check Slack app configuration and permissions.")
