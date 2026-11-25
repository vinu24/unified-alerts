"""Exception classes for unified-alerts."""


class AlertError(Exception):
    """Base exception for all unified-alerts errors."""


class ConfigurationError(AlertError):
    """Raised when an alert driver or manager configuration is invalid or missing."""


class DriverDeliveryError(AlertError):
    """Raised or logged when an underlying provider (Slack, Telegram) fails to deliver."""

    def __init__(self, driver: str, message: str, status_code: int | None = None, response: str | None = None) -> None:
        super().__init__(f"[{driver}] Delivery failed: {message}")
        self.driver = driver
        self.message = message
        self.status_code = status_code
        self.response = response
