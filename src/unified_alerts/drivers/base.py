"""Base alert driver interface."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from unified_alerts.message import AlertMessage


class BaseDriver(ABC):
    """Abstract interface that all alert notification drivers must implement."""

    name: str

    def __init__(self, **kwargs: Any) -> None:
        self.config = kwargs

    @abstractmethod
    def send(self, message: "AlertMessage") -> bool:
        """Send an alert message.
        
        Returns:
            True if delivered successfully, False otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def test_connection(self) -> dict[str, Any]:
        """Verify driver credentials and connectivity with the remote service.
        
        Returns:
            Dictionary with 'ok': bool, 'status': str, 'error': optional error details.
        """
        raise NotImplementedError
