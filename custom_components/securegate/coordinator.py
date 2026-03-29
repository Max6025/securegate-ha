"""DataUpdateCoordinator for SecureGate v3 — Multi-Room + Events + Weather."""
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
    """Fetch data from all SecureGate rooms + admin."""

    def __init__(self, hass: HomeAssistant, host: str, rooms: list[dict], scan_interval: int) -> None:
        self.host = host
        self.rooms = rooms
        self._prev_events = {}  # Track last event per room for HA event firing
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=scan_interval))

    async def _async_update_data(self) -> dict[str, Any]:
        result = {"rooms": {}, "admin": {}, "weather": {}, "events": [], "statistics": {}}
        try:
            async with async_timeout.timeout(20):
                async with aiohttp.ClientSession() as session:
                    for room in self.rooms:
                        port = room["port"]
                        name = room["name"]
                        try:
                            async with session.get(f"http://{self.host}:{port}/json", timeout=aiohttp.ClientTimeout(total=4)) as resp:
                                if resp.status == 200:
                                    data = await resp.json()
                                    data["_room_name"] = name
                                    data["_port"] = port
                                    data["_online"] = True
                                else:
                                    data = {"_room_name": name, "_port": port, "_online": False}
                            try:
                                async with session.get(f"http://{self.host}:{port}/api/config", timeout=aiohttp.ClientTimeout(total=3)) as resp2:
                                    if resp2.status == 200:
                                        data["_config"] = await resp2.json()
                            except Exception:
                                pass
                            result["rooms"][port] = data

                            # Fire HA event on new scan
                            ev = data.get("event", {})
                            ev_key = f"{port}_{ev.get('name', '')}_{ev.get('time', '')}"
                            if ev.get("name") and ev_key != self._prev_events.get(port):
                                self._prev_events[port] = ev_key
                                self.hass.bus.async_fire(f"{DOMAIN}_scan", {
                                    "room": name, "port": port,
                                    "type": ev.get("type", ""), "name": ev.get("name", ""),
                                    "level": ev.get("level", 0), "time": ev.get("time", ""),
                                    "atr": ev.get("atr", ""), "avatar": ev.get("avatar", ""),
                                    "blacklisted": ev.get("blacklisted", False),
                                    "is_guest": ev.get("is_guest", False),
                                })
                        except Exception as e:
                            result["rooms"][port] = {"_room_name": name, "_port": port, "_online": False, "_error": str(e)}

                    # Weather from first online room
                    for port, rd in result["rooms"].items():
                        if rd.get("_online"):
                            try:
                                async with session.get(f"http://{self.host}:{port}/api/weather", timeout=aiohttp.ClientTimeout(total=3)) as wr:
                                    if wr.status == 200:
                                        result["weather"] = await wr.json()
                            except Exception:
                                pass
                            break

                    # Events from admin
                    try:
                        async with session.get(f"http://{self.host}/admin/?api=events_list", timeout=aiohttp.ClientTimeout(total=4)) as er:
                            if er.status == 200:
                                edata = await er.json()
                                result["events"] = edata if isinstance(edata, list) else edata.get("events", [])
                    except Exception:
                        pass

                    # Statistics from admin
                    try:
                        async with session.get(f"http://{self.host}/admin/?api=stats", timeout=aiohttp.ClientTimeout(total=4)) as sr:
                            if sr.status == 200:
                                result["statistics"] = await sr.json()
                    except Exception:
                        pass

                    # Admin aggregates
                    total_users = sum(r.get("active_users", 0) for r in result["rooms"].values())
                    total_guests = sum(r.get("active_guests", 0) for r in result["rooms"].values())
                    total_logins = sum(r.get("today_total", 0) for r in result["rooms"].values())
                    online = sum(1 for r in result["rooms"].values() if r.get("_online"))
                    locked = sum(1 for r in result["rooms"].values() if r.get("system_locked"))
                    maint = sum(1 for r in result["rooms"].values() if r.get("maintenance_mode"))
                    result["admin"] = {
                        "total_active_users": total_users, "total_active_guests": total_guests,
                        "total_logins_today": total_logins, "rooms_online": online,
                        "rooms_total": len(self.rooms), "rooms_locked": locked, "rooms_maintenance": maint,
                    }
        except Exception as err:
            raise UpdateFailed(f"Error: {err}") from err
        return result

    async def api_post(self, port: int, path: str, data: dict | None = None) -> dict:
        try:
            async with async_timeout.timeout(5):
                async with aiohttp.ClientSession() as session:
                    async with session.post(f"http://{self.host}:{port}{path}", json=data or {}, headers={"Content-Type": "application/json"}) as resp:
                        try:
                            return await resp.json()
                        except Exception:
                            return {"ok": resp.status == 200, "msg": await resp.text()}
        except Exception as err:
            _LOGGER.error("POST %s:%s%s failed: %s", self.host, port, path, err)
            return {"ok": False, "msg": str(err)}

    async def api_post_all(self, path: str, data: dict | None = None) -> list[dict]:
        results = []
        for room in self.rooms:
            results.append(await self.api_post(room["port"], path, data))
        return results
