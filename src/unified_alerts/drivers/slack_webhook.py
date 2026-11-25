"""Slack Incoming Webhook alert driver."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any

from unified_alerts.drivers.base import BaseDriver
from unified_alerts.exceptions import ConfigurationError
from unified_alerts.message import AlertMessage

logger = logging.getLogger("unified_alerts.slack_webhook")


def escape_mrkdwn(text: str) -> str:
    """Escape control characters in Slack mrkdwn."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class SlackWebhookDriver(BaseDriver):
    """Sends alert notifications through a Slack Incoming Webhook URL."""

    name = "slack_webhook"

    def __init__(self, webhook_url: str, timeout: float = 10.0, **kwargs: Any) -> None:
        super().__init__(webhook_url=webhook_url, timeout=timeout, **kwargs)
        if not webhook_url:
            raise ConfigurationError("SlackWebhookDriver requires a non-empty 'webhook_url'")
        self.webhook_url = webhook_url
        self.timeout = float(timeout)

    def _build_payload(self, message: AlertMessage) -> dict[str, Any]:
        """Construct a structured Slack Block Kit message."""
        title_text = f"{message.level.emoji} *{escape_mrkdwn(message.title)}*"

        blocks: list[dict[str, Any]] = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": title_text},
            }
        ]

        if message.text:
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": escape_mrkdwn(message.text)},
            })

        if message.fields:
            fields_data = [
                {"type": "mrkdwn", "text": f"*{escape_mrkdwn(f.label)}:*\n{escape_mrkdwn(f.value)}"}
                for f in message.fields
            ]
            # Slack section blocks accept up to 10 fields per block
            for i in range(0, len(fields_data), 10):
                blocks.append({
                    "type": "section",
                    "fields": fields_data[i : i + 10],
                })

        if message.actions:
            elements = [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": a.text[:75]},
                    "url": a.url,
                }
                for a in message.actions[:5]
            ]
            blocks.append({"type": "actions", "elements": elements})

        # Wrap in color attachment matching level
        return {
            "attachments": [
                {
                    "color": message.level.color_hex,
                    "blocks": blocks,
                }
            ],
            "unfurl_links": False,
        }

    def send(self, message: AlertMessage) -> bool:
        """Send message to the webhook URL."""
        payload = self._build_payload(message)
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.webhook_url,
            data=body,
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                status = resp.status
                return 200 <= status < 300
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            logger.error(
                "Slack Webhook failed with HTTP %d: %s", exc.code, error_body
            )
            return False
        except Exception as exc:
            logger.error("Slack Webhook connection failed: %s", exc)
            return False

    def test_connection(self) -> dict[str, Any]:
        """Test the webhook URL with a lightweight validation alert."""
        from unified_alerts.message import Alert

        sample = Alert.info("Test Alert", "Unified Alerts connection verified successfully.")
        ok = self.send(sample)
        return {
            "ok": ok,
            "driver": self.name,
            "status": "connected" if ok else "delivery_failed",
        }
