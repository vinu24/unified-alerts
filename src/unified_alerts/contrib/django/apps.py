try:
    from django.apps import AppConfig
    from django.conf import settings
except ImportError:
    AppConfig = object  # type: ignore


class UnifiedAlertsConfig(AppConfig):
    name = "unified_alerts.contrib.django"
    label = "unified_alerts"
    verbose_name = "Unified Alerts"

    def ready(self):
        from unified_alerts.manager import get_default_manager

        if hasattr(settings, "UNIFIED_ALERTS"):
            get_default_manager().configure(settings.UNIFIED_ALERTS)
