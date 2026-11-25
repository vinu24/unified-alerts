try:
    from django.core.management.base import BaseCommand
except ImportError:
    BaseCommand = object  # type: ignore


class Command(BaseCommand):
    help = "Test configured alert drivers and dispatch a sample test alert."

    def add_arguments(self, parser):
        parser.add_argument("--driver", type=str, help="Specific driver to test")
        parser.add_argument("--send", action="store_true", help="Send actual test message")

    def handle(self, *args, **options):
        from unified_alerts.manager import get_default_manager
        from unified_alerts.message import Alert

        manager = get_default_manager()
        driver = options.get("driver")

        self.stdout.write("Testing alert connections...")
        results = manager.test(driver)

        for name, (ok, text) in results.items():
            status = self.style.SUCCESS("[OK]") if ok else self.style.ERROR("[FAIL]")
            self.stdout.write(f"  {status} {name}: {text}")

        if options.get("send"):
            self.stdout.write("\nDispatching sample alert...")
            send_results = (
                Alert.info("Unified Alerts Test")
                .field("Environment", "Django CLI Test")
                .field("Status", "Operational")
                .send()
            )
            for name, sent in send_results.items():
                s = self.style.SUCCESS("[SENT]") if sent else self.style.ERROR("[FAILED]")
                self.stdout.write(f"  {s} {name}")
