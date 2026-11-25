import unittest
from unittest.mock import patch

from unified_alerts.drivers.slack_bot import SlackBotDriver
from unified_alerts.drivers.slack_webhook import SlackWebhookDriver, escape_slack
from unified_alerts.message import Alert


class TestSlackDrivers(unittest.TestCase):
    def test_escape_slack(self):
        self.assertEqual(
            escape_slack("User <user@example.com> & 'Company'"),
            "User &lt;user@example.com&gt; &amp; 'Company'",
        )

    def test_slack_webhook_payload(self):
        driver = SlackWebhookDriver("https://hooks.slack.com/services/T00/B00/X00")
        msg = (
            Alert.error("Payment Failed")
            .field("Amount", "$99")
            .action("Retry", "https://example.com/retry")
        )
        payload = driver._build_payload(msg)

        self.assertIn("blocks", payload)
        self.assertFalse(payload["unfurl_links"])
        self.assertEqual(payload["blocks"][0]["type"], "header")
        self.assertIn("Payment Failed", payload["blocks"][0]["text"]["text"])
        self.assertEqual(payload["blocks"][1]["fields"][0]["text"], "*Amount:*\n$99")
        self.assertEqual(payload["blocks"][2]["elements"][0]["url"], "https://example.com/retry")

    def test_slack_webhook_send_success(self):
        driver = SlackWebhookDriver("https://hooks.slack.com/services/T00/B00/X00")
        msg = Alert.info("Deploy OK")

        with patch.object(driver, "_http_post", return_value=(200, "ok")):
            self.assertTrue(driver.send(msg))

    def test_slack_webhook_send_failure(self):
        driver = SlackWebhookDriver("https://hooks.slack.com/services/T00/B00/X00")
        msg = Alert.info("Deploy OK")

        with patch.object(driver, "_http_post", return_value=(404, "channel_not_found")):
            self.assertFalse(driver.send(msg))

    def test_slack_bot_driver_send(self):
        driver = SlackBotDriver("xoxb-123456789-test", default_channel="#alerts")
        msg = Alert.warning("Warning alert").channel("#custom-channel")

        with patch.object(driver, "_http_post", return_value=(200, {"ok": True})) as mock_post:
            self.assertTrue(driver.send(msg))
            mock_post.assert_called_once()
            _, payload = mock_post.call_args[0][:2]
            self.assertEqual(payload["channel"], "custom-channel")

    def test_slack_bot_invalid_token(self):
        with self.assertRaises(ValueError):
            SlackBotDriver("invalid-token", default_channel="alerts")


if __name__ == "__main__":
    unittest.main()
