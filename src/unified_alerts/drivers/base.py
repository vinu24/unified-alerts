"""Base alert driver interface."""

from abc import ABC, abstractmethod
import json
import logging
from typing import TYPE_CHECKING, Any
import urllib.error
import urllib.request

if TYPE_CHECKING:
    from unified_alerts.message import AlertMessage

logger = logging.getLogger("unified_alerts.drivers.base")


class BaseDriver(ABC):
    """Abstract interface that all alert notification drivers must implement."""

    name: str

    def __init__(self, **kwargs: Any) -> None:
        self.config = kwargs

    def _http_post(
        self,
        url: str,
        payload: dict[str, Any] | str,
        headers: dict[str, str] | None = None,
        timeout: float = 10.0,
    ) -> tuple[int, Any]:
        """Execute an HTTP POST request using standard library urllib.
        
        Returns:
            Tuple of (status_code, parsed_response_data)
        """
        hdrs = {"Content-Type": "application/json; charset=utf-8"}
        if headers:
            hdrs.update(headers)

        if isinstance(payload, str):
            data_bytes = payload.encode("utf-8")
        else:
            data_bytes = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(url, data=data_bytes, headers=hdrs)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status = resp.status
                content = resp.read().decode("utf-8")
                try:
                    parsed = json.loads(content)
                except Exception:
                    parsed = content
                return status, parsed
        except urllib.error.HTTPError as exc:
            err_content = exc.read().decode("utf-8") if exc.fp else ""
            try:
                parsed = json.loads(err_content)
            except Exception:
                parsed = err_content or exc.reason
            return exc.code, parsed
        except Exception as exc:
            logger.error("HTTP POST request failed: %s", exc)
            return 0, str(exc)

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
