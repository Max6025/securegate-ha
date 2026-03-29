"""DataUpdateCoordinator for SecureGate — Multi-Room."""
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
    """Fetch data from all SecureGate rooms."""

    def __init__(self, hass: HomeAssistant, host: str, rooms: list[dict], scan_interval: int) -> None:
        self.host = host
        self.rooms = rooms  # [{"name": "Haus Tür", "port": 5000}, ...]
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=scan_interval))

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from all rooms."""
        result = {"rooms": {}, "admin": {}}
        try:
            async with async_timeout.timeout(15):
                async with aiohttp.ClientSession() as session:
                    for room in self.rooms:
                        port = room["port"]
                        name = room["name"]
                        try:
                            # /json — live data
                            async with session.get(f"http://{self.host}:{port}/json", timeout=aiohttp.ClientTimeout(total=4)) as resp:
                                if resp.status == 200:
                                    data = await resp.json()
                                    data["_room_name"] = name
                                    data["_port"] = port
                                    data["_online"] = True
                                else:
                                    data = {"_room_name": name, "_port": port, "_online": False}
                            # /api/config — settings
                            try:
                                async with session.get(f"http://{self.host}:{port}/api/config", timeout=aiohttp.ClientTimeout(total=3)) as resp2:
                                    if resp2.status == 200:
                                        data["_config"] = await resp2.json()
                            except Exception:
                                pass
                            result["rooms"][port] = data
                        except Exception as e:
                            result["rooms"][port] = {"_room_name": name, "_port": port, "_online": False, "_error": str(e)}

                    # Admin summary
                    total_users = sum(r.get("active_users", 0) for r in result["rooms"].values())
                    total_guests = sum(r.get("active_guests", 0) for r in result["rooms"].values())
                    total_logins = sum(r.get("today_total", 0) for r in result["rooms"].values())
                    online_rooms = sum(1 for r in result["rooms"].values() if r.get("_online"))
                    locked_rooms = sum(1 for r in result["rooms"].values() if r.get("system_locked"))
                    maint_rooms = sum(1 for r in result["rooms"].values() if r.get("maintenance_mode"))
                    result["admin"] = {
                        "total_active_users": total_users,
                        "total_active_guests": total_guests,
                        "total_logins_today": total_logins,
                        "rooms_online": online_rooms,
                        "rooms_total": len(self.rooms),
                        "rooms_locked": locked_rooms,
                        "rooms_maintenance": maint_rooms,
                    }
        except Exception as err:
            raise UpdateFailed(f"Error: {err}") from err
        return result

    async def api_post(self, port: int, path: str, data: dict | None = None) -> dict:
        """POST to a specific room."""
        try:
            async with async_timeout.timeout(5):
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"http://{self.host}:{port}{path}",
                        json=data or {},
                        headers={"Content-Type": "application/json"},
                    ) as resp:
                        return await resp.json()
        except Exception as err:
            _LOGGER.error("API POST %s:%s%s failed: %s", self.host, port, path, err)
            return {"ok": False, "msg": str(err)}

    async def api_post_all(self, path: str, data: dict | None = None) -> list[dict]:
        """POST to all rooms."""
        results = []
        for room in self.rooms:
            r = await self.api_post(room["port"], path, data)
            results.append(r)
        return results
