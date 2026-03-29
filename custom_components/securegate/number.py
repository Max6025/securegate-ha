"""Number platform for SecureGate v3 — Access time settings."""
from __future__ import annotations
from homeassistant.components.number import NumberEntity, NumberMode
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
    entities = []
    for room in rooms:
        p, n = room["port"], room["name"]
        entities.extend([
            RoomAccessHourFrom(coordinator, p, n),
            RoomAccessHourTo(coordinator, p, n),
        ])
    async_add_entities(entities)


class RoomAccessHourFrom(CoordinatorEntity[SecureGateCoordinator], NumberEntity):
    """Access time start hour."""
    def __init__(self, coordinator, port, room_name):
        super().__init__(coordinator)
        self._port, self._room_name = port, room_name
        self._attr_unique_id = f"sg_{port}_access_hour_from"
        self._attr_name = f"{room_name} Zugang Von (Stunde)"
        self._attr_icon = "mdi:clock-start"
        self._attr_native_min_value = 0
        self._attr_native_max_value = 23
        self._attr_native_step = 1
        self._attr_mode = NumberMode.SLIDER

    @property
    def device_info(self): return device_room(self.coordinator, self._port, self._room_name)

    @property
    def native_value(self):
        cfg = self.coordinator.data.get("rooms", {}).get(self._port, {}).get("_config", {})
        tf = cfg.get("access_time_from", "")
        if tf:
            try: return int(tf.split(":")[0])
            except Exception: pass
        return None

    async def async_set_native_value(self, value: float) -> None:
        h = int(value)
        cfg = self.coordinator.data.get("rooms", {}).get(self._port, {}).get("_config", {})
        current_to = cfg.get("access_time_to", "20:00")
        new_from = f"{h:02d}:00"
        await self.coordinator.api_post(self._port, "/api/settings", {"access_time_from": new_from, "access_time_to": current_to, "access_time_enabled": True})
        await self.coordinator.async_request_refresh()

    @property
    def available(self): return self.coordinator.data.get("rooms", {}).get(self._port, {}).get("_online", False)


class RoomAccessHourTo(CoordinatorEntity[SecureGateCoordinator], NumberEntity):
    """Access time end hour."""
    def __init__(self, coordinator, port, room_name):
        super().__init__(coordinator)
        self._port, self._room_name = port, room_name
        self._attr_unique_id = f"sg_{port}_access_hour_to"
        self._attr_name = f"{room_name} Zugang Bis (Stunde)"
        self._attr_icon = "mdi:clock-end"
        self._attr_native_min_value = 0
        self._attr_native_max_value = 23
        self._attr_native_step = 1
        self._attr_mode = NumberMode.SLIDER

    @property
    def device_info(self): return device_room(self.coordinator, self._port, self._room_name)

    @property
    def native_value(self):
        cfg = self.coordinator.data.get("rooms", {}).get(self._port, {}).get("_config", {})
        tt = cfg.get("access_time_to", "")
        if tt:
            try: return int(tt.split(":")[0])
            except Exception: pass
        return None

    async def async_set_native_value(self, value: float) -> None:
        h = int(value)
        cfg = self.coordinator.data.get("rooms", {}).get(self._port, {}).get("_config", {})
        current_from = cfg.get("access_time_from", "07:00")
        new_to = f"{h:02d}:00"
        await self.coordinator.api_post(self._port, "/api/settings", {"access_time_from": current_from, "access_time_to": new_to, "access_time_enabled": True})
        await self.coordinator.async_request_refresh()

    @property
    def available(self): return self.coordinator.data.get("rooms", {}).get(self._port, {}).get("_online", False)
