"""Telegram Bot API alert driver with HTML formatting and inline keyboard buttons."""

from __future__ import annotations

import html
import json
import logging
import urllib.error
import urllib.request
from typing import Any

from unified_alerts.drivers.base import BaseDriver
from unified_alerts.exceptions import ConfigurationError
from unified_alerts.message import AlertMessage

logger = logging.getLogger("unified_alerts.telegram")

TELEGRAM_API_BASE = "https://api.telegram.org"


class TelegramDriver(BaseDriver):
    """Sends alert notifications through Telegram Bot API."""

    name = "telegram"

    def __init__(
        self,
        bot_token: str | None = None,
        default_chat_id: str | int | None = None,
        timeout: float = 10.0,
        token: str | None = None,
        chat_id: str | int | None = None,
        **kwargs: Any,
    ) -> None:
        raw_token = (bot_token or token or "").strip()
        raw_chat = default_chat_id if default_chat_id is not None else chat_id
        super().__init__(
            bot_token=raw_token,
            default_chat_id=raw_chat,
            timeout=timeout,
            **kwargs,
        )
        if not raw_token or ":" not in raw_token or not raw_token.split(":", 1)[0].isdigit():
            raise ConfigurationError("TelegramDriver requires a valid bot token in '<bot_id>:<token>' format")
        if raw_chat is None or str(raw_chat).strip() == "":
            raise ConfigurationError("TelegramDriver requires a non-empty 'default_chat_id'")

        self.bot_token = raw_token
        self.default_chat_id = str(raw_chat).strip()
        self.timeout = float(timeout)

    @property
    def _send_message_url(self) -> str:
        return f"{TELEGRAM_API_BASE}/bot{self.bot_token}/sendMessage"

    @property
    def _get_me_url(self) -> str:
        return f"{TELEGRAM_API_BASE}/bot{self.bot_token}/getMe"

    def _build_html_text(self, message: AlertMessage) -> str:
        """Construct Telegram HTML text with proper escaping."""
        parts: list[str] = [
            f"{message.level.emoji} <b>{html.escape(message.title)}</b>"
        ]

        if message.text:
            parts.append(html.escape(message.text))

        if message.fields:
            field_lines = [
                f"• <b>{html.escape(f.label)}:</b> {html.escape(f.value)}"
                for f in message.fields
            ]
            parts.append("\n".join(field_lines))

        return "\n\n".join(parts)

    def _build_reply_markup(self, message: AlertMessage) -> dict[str, Any] | None:
        """Create an inline keyboard markup for action buttons."""
        if not message.actions:
            return None

        keyboard = [
            [{"text": action.text[:64], "url": action.url}]
            for action in message.actions[:5]
        ]
        return {"inline_keyboard": keyboard}

    def send(self, message: AlertMessage) -> bool:
        """Send message using Telegram's sendMessage endpoint."""
        target_chat = str(message.target_channel or self.default_chat_id).strip()

        payload: dict[str, Any] = {
            "chat_id": target_chat,
            "text": self._build_html_text(message),
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }

        markup = self._build_reply_markup(message)
        if markup:
            payload["reply_markup"] = markup

        status, data = self._http_post(
            self._send_message_url,
            payload,
            timeout=self.timeout,
        )

        if status == 200 and isinstance(data, dict) and data.get("ok"):
            return True

        if isinstance(data, dict):
            err_desc = data.get("description", "Unknown Telegram error")
            err_code = data.get("error_code", status)
            logger.error(
                "Telegram delivery to %s failed [%s]: %s (%s)",
                target_chat,
                err_code,
                err_desc,
                self._diagnose_error(err_desc),
            )
        else:
            logger.error("Telegram delivery to %s failed [%d]: %s", target_chat, status, data)
        return False

    def test_connection(self) -> dict[str, Any]:
        """Verify bot token validity without posting a message."""
        req = urllib.request.Request(self._get_me_url)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8") or "{}")

            if data.get("ok"):
                bot_info = data.get("result", {})
                return {
                    "ok": True,
                    "driver": self.name,
                    "status": "connected",
                    "bot_id": bot_info.get("id"),
                    "bot_name": bot_info.get("first_name"),
                    "username": f"@{bot_info.get('username')}",
                    "default_chat_id": self.default_chat_id,
                }

            desc = data.get("description", "Authentication failed")
            return {
                "ok": False,
                "driver": self.name,
                "status": "auth_failed",
                "error": desc,
                "hint": self._diagnose_error(desc),
            }
        except Exception as exc:
            return {
                "ok": False,
                "driver": self.name,
                "status": "connection_error",
                "error": str(exc),
            }

    @staticmethod
    def _diagnose_error(desc: str) -> str:
        """Provide helpful diagnosis for common Telegram errors."""
        desc_lower = desc.lower()
        if "chat not found" in desc_lower:
            return "Make sure the chat_id is correct and the bot has been added to the chat/group."
        if "bot was blocked by the user" in desc_lower:
            return "The user has blocked or not yet started a conversation with the bot."
        if "unauthorized" in desc_lower:
            return "Bot token is invalid. Re-check the token received from @BotFather."
        if "not enough rights" in desc_lower or "need administrator rights" in desc_lower:
            return "The bot needs Administrator privileges in the target channel or supergroup."
        return "Check bot permissions and target chat ID."
