"""SSH connection lifecycle: connect, retry, timeout, disconnect."""

from contextlib import contextmanager
from typing import Any, Iterator

from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoAuthenticationException, NetmikoTimeoutException

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


def build_device_params(
    hostname: str,
    mgmt_ip: str,
    platform: str,
    credentials: dict[str, str],
    timeout: int = 30,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "device_type": platform,
        "host": mgmt_ip,
        "username": credentials["username"],
        "password": credentials["password"],
        "timeout": timeout,
        "conn_timeout": timeout,
        "fast_cli": False,
    }
    if credentials.get("secret"):
        params["secret"] = credentials["secret"]
    return params


@contextmanager
def open_connection(device_params: dict[str, Any]) -> Iterator[Any]:
    connection = None
    try:
        connection = ConnectHandler(**device_params)
        if device_params.get("secret"):
            try:
                connection.enable()
            except Exception as exc:
                logger.warning(
                    "Enable mode failed for %s: %s",
                    device_params.get("host"),
                    exc,
                )
        yield connection
    finally:
        if connection is not None:
            connection.disconnect()


def connect_with_retry(
    device_params: dict[str, Any],
    retries: int = 2,
) -> Any:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            connection = ConnectHandler(**device_params)
            if device_params.get("secret"):
                try:
                    connection.enable()
                except Exception:
                    pass
            return connection
        except (NetmikoTimeoutException, NetmikoAuthenticationException) as exc:
            last_error = exc
            logger.warning(
                "Connection attempt %s failed for %s: %s",
                attempt,
                device_params.get("host"),
                exc,
            )
    raise ConnectionError(
        f"Unable to connect to {device_params.get('host')}: {last_error}"
    ) from last_error
