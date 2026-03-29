"""DataUpdateCoordinator for SecureGate."""
import logging
from datetime import timedelta
from typing import Any

import aiohttp
import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class SecureGateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch data from SecureGate API."""

    def __init__(self, hass: HomeAssistant, host: str, port: int, scan_interval: int) -> None:
        """Initialize."""
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from SecureGate."""
        try:
            async with async_timeout.timeout(8):
                async with aiohttp.ClientSession() as session:
                    # Fetch /json (live data)
                    async with session.get(f"{self.base_url}/json") as resp:
                        if resp.status != 200:
                            raise UpdateFailed(f"API error: {resp.status}")
                        json_data = await resp.json()

                    # Fetch /api/config (settings)
                    try:
                        async with session.get(f"{self.base_url}/api/config") as resp2:
                            if resp2.status == 200:
                                config_data = await resp2.json()
                                json_data["_config"] = config_data
                    except Exception:
                        pass

                    return json_data

        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Connection error: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Error: {err}") from err

    async def api_post(self, path: str, data: dict | None = None) -> dict:
        """Send POST request to SecureGate API."""
        try:
            async with async_timeout.timeout(5):
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}{path}",
                        json=data or {},
                        headers={"Content-Type": "application/json"},
                    ) as resp:
                        return await resp.json()
        except Exception as err:
            _LOGGER.error("API POST %s failed: %s", path, err)
            return {"ok": False, "msg": str(err)}
