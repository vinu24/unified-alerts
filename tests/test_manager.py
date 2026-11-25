import os
import unittest
from unittest.mock import patch

from unified_alerts.drivers.memory import MemoryDriver
from unified_alerts.manager import AlertManager
from unified_alerts.message import Alert


class TestAlertManager(unittest.TestCase):
    def test_manager_dispatch_to_multiple_drivers(self):
        mem1 = MemoryDriver()
        mem2 = MemoryDriver()

        mgr = AlertManager()
        mgr.register("slack", mem1, as_default=True)
        mgr.register("telegram", mem2, as_default=True)

        results = Alert.info("Broadcasting").send(manager=mgr)

        self.assertEqual(results, {"slack": True, "telegram": True})
        self.assertEqual(len(mem1.outbox), 1)
        self.assertEqual(len(mem2.outbox), 1)
        self.assertEqual(mem1.outbox[0].title, "Broadcasting")

    def test_manager_selective_driver_dispatch(self):
        mem1 = MemoryDriver()
        mem2 = MemoryDriver()

        mgr = AlertManager()
        mgr.register("slack", mem1, as_default=True)
        mgr.register("telegram", mem2, as_default=True)

        msg = Alert.warning("Only to Telegram")
        results = mgr.send(msg, drivers=["telegram"])

        self.assertEqual(results, {"telegram": True})
        self.assertEqual(len(mem1.outbox), 0)
        self.assertEqual(len(mem2.outbox), 1)

    def test_manager_handles_driver_exceptions_gracefully(self):
        class BrokenDriver(MemoryDriver):
            def send(self, message):
                raise ConnectionError("Network down")

        broken = BrokenDriver()
        healthy = MemoryDriver()

        mgr = AlertManager()
        mgr.register("broken", broken, as_default=True)
        mgr.register("healthy", healthy, as_default=True)

        # Must never raise an unhandled exception
        results = mgr.send(Alert.error("Test Error"))
        self.assertEqual(results, {"broken": False, "healthy": True})
        self.assertEqual(len(healthy.outbox), 1)

    def test_manager_from_env_memory_mode(self):
        with patch.dict(os.environ, {"ALERTS_BACKEND": "memory"}):
            mgr = AlertManager.from_env()
            driver = mgr.get_driver("memory")
            self.assertIsNotNone(driver)
            self.assertIsInstance(driver, MemoryDriver)


if __name__ == "__main__":
    unittest.main()
