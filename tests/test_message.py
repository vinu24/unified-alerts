import unittest

from unified_alerts.enums import AlertLevel
from unified_alerts.message import Alert


class TestAlertMessage(unittest.TestCase):
    def test_alert_message_fluent_builder(self):
        msg = (
            Alert.warning("Database High Latency")
            .field("Host", "db-primary-01")
            .field("Latency", "1,420 ms")
            .fields_dict({"Region": "eu-west-1", "Pool": "read"})
            .action("View Metrics", "https://metrics.example.com")
            .channel("#ops", "@alerts_group")
            .meta("retry_count", 2)
        )

        self.assertEqual(msg.title, "Database High Latency")
        self.assertEqual(msg.level, AlertLevel.WARNING)
        self.assertEqual(msg.level.emoji, "⚠️")
        self.assertEqual(len(msg.fields), 4)
        self.assertEqual(msg.fields[0].label, "Host")
        self.assertEqual(msg.fields[0].value, "db-primary-01")
        self.assertEqual(msg.fields[2].label, "Region")
        self.assertEqual(msg.fields[2].value, "eu-west-1")
        self.assertEqual(len(msg.actions), 1)
        self.assertEqual(msg.actions[0].label, "View Metrics")
        self.assertEqual(msg.actions[0].url, "https://metrics.example.com")
        self.assertEqual(msg.channels, ["#ops", "@alerts_group"])
        self.assertEqual(msg.metadata["retry_count"], 2)

    def test_alert_factory_methods(self):
        info = Alert.info("Info Title")
        self.assertEqual(info.level, AlertLevel.INFO)

        success = Alert.success("Success Title")
        self.assertEqual(success.level, AlertLevel.SUCCESS)

        warn = Alert.warning("Warning Title")
        self.assertEqual(warn.level, AlertLevel.WARNING)

        err = Alert.error("Error Title")
        self.assertEqual(err.level, AlertLevel.ERROR)

        crit = Alert.critical("Critical Title")
        self.assertEqual(crit.level, AlertLevel.CRITICAL)


if __name__ == "__main__":
    unittest.main()
