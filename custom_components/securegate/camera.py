"""Camera platform for SecureGate v3 — Last scan avatar."""
from __future__ import annotations
import logging

import aiohttp
import async_timeout

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN
from .coordinator import SecureGateCoordinator
from .helpers import device_room

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    rooms = entry.data.get("rooms", [])
    entities = [RoomLastScanCamera(coordinator, r["port"], r["name"]) for r in rooms]
    async_add_entities(entities)


class RoomLastScanCamera(CoordinatorEntity[SecureGateCoordinator], Camera):
    """Shows the avatar of the last scanned user."""

    def __init__(self, coordinator, port, room_name):
        CoordinatorEntity.__init__(self, coordinator)
        Camera.__init__(self)
        self._port = port
        self._room_name = room_name
        self._attr_unique_id = f"sg_{port}_last_scan_cam"
        self._attr_name = f"{room_name} Letzter Scan"
        self._attr_icon = "mdi:account-box"
        self._last_avatar = None
        self._image_cache = None

    @property
    def device_info(self):
        return device_room(self.coordinator, self._port, self._room_name)

    @property
    def is_streaming(self):
        return False

    @property
    def extra_state_attributes(self):
        ev = self.coordinator.data.get("rooms", {}).get(self._port, {}).get("event", {})
        return {"name": ev.get("name", ""), "type": ev.get("type", ""), "time": ev.get("time", "")}

    async def async_camera_image(self, width=None, height=None):
        """Return avatar image of last scanned user."""
        ev = self.coordinator.data.get("rooms", {}).get(self._port, {}).get("event", {})
        avatar = ev.get("avatar", "")
        if not avatar:
            return None
        # Cache
        if avatar == self._last_avatar and self._image_cache:
            return self._image_cache
        try:
            async with async_timeout.timeout(5):
                async with aiohttp.ClientSession() as session:
                    url = f"http://{self.coordinator.host}/admin/?api=reader_avatar&f={avatar}"
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            self._image_cache = await resp.read()
                            self._last_avatar = avatar
                            return self._image_cache
        except Exception as e:
            _LOGGER.debug("Camera fetch failed: %s", e)
        return None

    @property
    def available(self):
        return self.coordinator.data.get("rooms", {}).get(self._port, {}).get("_online", False)
