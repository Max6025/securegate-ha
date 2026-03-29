"""Event platform for SecureGate v3 — Real-time scan events."""
from __future__ import annotations
from homeassistant.components.event import EventEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN
from .coordinator import SecureGateCoordinator
from .helpers import device_room


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    rooms = entry.data.get("rooms", [])
    entities = [RoomScanEvent(coordinator, r["port"], r["name"]) for r in rooms]
    async_add_entities(entities)


class RoomScanEvent(CoordinatorEntity[SecureGateCoordinator], EventEntity):
    """Fires event on each NFC scan."""

    _attr_event_types = ["check_in", "check_out", "denied", "unknown", "blacklisted", "lockdown_scan"]

    def __init__(self, coordinator, port, room_name):
        super().__init__(coordinator)
        self._port = port
        self._room_name = room_name
        self._attr_unique_id = f"sg_{port}_scan_event"
        self._attr_name = f"{room_name} Scan Event"
        self._attr_icon = "mdi:nfc-tap"
        self._last_event_key = None

    @property
    def device_info(self):
        return device_room(self.coordinator, self._port, self._room_name)

    def _async_handle_coordinator_update(self) -> None:
        """Handle updated data — fire event if new scan detected."""
        ev = self.coordinator.data.get("rooms", {}).get(self._port, {}).get("event", {})
        if not ev or not ev.get("name"):
            super()._async_handle_coordinator_update()
            return

        key = f"{ev.get('name', '')}_{ev.get('time', '')}_{ev.get('type', '')}"
        if key != self._last_event_key:
            self._last_event_key = key
            event_type = self._map_event_type(ev.get("type", ""))
            self._trigger_event(event_type, {
                "name": ev.get("name", ""),
                "level": ev.get("level", 0),
                "atr": ev.get("atr", ""),
                "time": ev.get("time", ""),
                "avatar": ev.get("avatar", ""),
                "is_guest": ev.get("is_guest", False),
                "blacklisted": ev.get("blacklisted", False),
            })
        super()._async_handle_coordinator_update()

    @staticmethod
    def _map_event_type(raw: str) -> str:
        raw_lower = raw.lower().strip()
        if "check-in" in raw_lower or "checkin" in raw_lower or "login" in raw_lower: return "check_in"
        if "check-out" in raw_lower or "checkout" in raw_lower or "logout" in raw_lower: return "check_out"
        if "denied" in raw_lower or "verweigert" in raw_lower: return "denied"
        if "blacklist" in raw_lower: return "blacklisted"
        if "lockdown" in raw_lower: return "lockdown_scan"
        if "unknown" in raw_lower or "unbekannt" in raw_lower: return "unknown"
        return "check_in"

    @property
    def available(self):
        return self.coordinator.data.get("rooms", {}).get(self._port, {}).get("_online", False)
