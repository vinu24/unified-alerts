import unittest
from unittest.mock import patch

from unified_alerts.drivers.telegram import TelegramDriver
from unified_alerts.message import Alert


class TestTelegramDriver(unittest.TestCase):
    def test_telegram_driver_validation(self):
        with self.assertRaises(ValueError):
            TelegramDriver("badtoken", default_chat_id="12345")

    def test_telegram_driver_html_formatting(self):
        driver = TelegramDriver("123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11", default_chat_id="-100987654321")
        msg = (
            Alert.error("System Crash")
            .field("Service", "auth <v2>")
            .action("Dashboard", "https://example.com/dash")
        )
        html_text = driver._build_html_text(msg)

        self.assertIn("<b>System Crash</b>", html_text)
        self.assertIn("<b>Service:</b> auth &lt;v2&gt;", html_text)

        markup = driver._build_reply_markup(msg)
        self.assertEqual(markup, {"inline_keyboard": [[{"text": "Dashboard", "url": "https://example.com/dash"}]]})

    def test_telegram_driver_send(self):
        driver = TelegramDriver("123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11", default_chat_id="-100987654321")
        msg = Alert.info("Daily Summary")

        with patch.object(driver, "_http_post", return_value=(200, {"ok": True})) as mock_post:
            self.assertTrue(driver.send(msg))
            mock_post.assert_called_once()
            url, payload = mock_post.call_args[0][:2]
            self.assertTrue(url.endswith("/sendMessage"))
            self.assertEqual(payload["chat_id"], "-100987654321")
            self.assertEqual(payload["parse_mode"], "HTML")


if __name__ == "__main__":
    unittest.main()
