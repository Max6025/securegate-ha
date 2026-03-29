"""Switch platform for SecureGate — Multi-Room."""
from __future__ import annotations
import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN
from .coordinator import SecureGateCoordinator
from .sensor import _device_info_room, _device_info_admin

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    rooms = entry.data.get("rooms", [])
    entities = []
    for room in rooms:
        p, n = room["port"], room["name"]
        entities.extend([
            RoomLockdownSwitch(coordinator, p, n),
            RoomMaintenanceSwitch(coordinator, p, n),
        ])
    entities.append(AdminLockdownAllSwitch(coordinator))
    entities.append(AdminMaintenanceAllSwitch(coordinator))
    async_add_entities(entities)


class RoomLockdownSwitch(CoordinatorEntity[SecureGateCoordinator], SwitchEntity):
    def __init__(self, coordinator, port, room_name):
        super().__init__(coordinator)
        self._port = port
        self._room_name = room_name
        self._attr_unique_id = f"sg_{port}_lockdown_switch"
        self._attr_name = f"{room_name} Lockdown"
        self._attr_icon = "mdi:lock-alert"

    @property
    def device_info(self):
        return _device_info_room(self.coordinator, self._port, self._room_name)

    @property
    def is_on(self):
        r = self.coordinator.data.get("rooms", {}).get(self._port, {})
        return r.get("system_locked", False) and not r.get("maintenance_mode", False)

    async def async_turn_on(self, **kwargs):
        await self.coordinator.api_post(self._port, "/cmd", {"cmd": "lock"})
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self.coordinator.api_post(self._port, "/cmd", {"cmd": "unlock"})
        await self.coordinator.async_request_refresh()

    @property
    def available(self):
        return self.coordinator.data.get("rooms", {}).get(self._port, {}).get("_online", False)


class RoomMaintenanceSwitch(CoordinatorEntity[SecureGateCoordinator], SwitchEntity):
    def __init__(self, coordinator, port, room_name):
        super().__init__(coordinator)
        self._port = port
        self._room_name = room_name
        self._attr_unique_id = f"sg_{port}_maintenance_switch"
        self._attr_name = f"{room_name} Wartungsmodus"
        self._attr_icon = "mdi:wrench-cog"

    @property
    def device_info(self):
        return _device_info_room(self.coordinator, self._port, self._room_name)

    @property
    def is_on(self):
        return self.coordinator.data.get("rooms", {}).get(self._port, {}).get("maintenance_mode", False)

    async def async_turn_on(self, **kwargs):
        await self.coordinator.api_post(self._port, "/api/maintenance", {"action": "on", "duration": 0, "msg": "Via Home Assistant"})
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self.coordinator.api_post(self._port, "/api/maintenance", {"action": "off"})
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self):
        r = self.coordinator.data.get("rooms", {}).get(self._port, {})
        if r.get("maintenance_mode"):
            return {"message": r.get("maintenance_msg", ""), "remaining": round(r.get("maintenance_remain", 0))}
        return {}

    @property
    def available(self):
        return self.coordinator.data.get("rooms", {}).get(self._port, {}).get("_online", False)


class AdminLockdownAllSwitch(CoordinatorEntity[SecureGateCoordinator], SwitchEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = "sg_admin_lockdown_all"
        self._attr_name = "SecureGate Alle Lockdown"
        self._attr_icon = "mdi:lock-alert-outline"

    @property
    def device_info(self):
        return _device_info_admin(self.coordinator)

    @property
    def is_on(self):
        a = self.coordinator.data.get("admin", {})
        return a.get("rooms_locked", 0) > 0

    async def async_turn_on(self, **kwargs):
        await self.coordinator.api_post_all("/cmd", {"cmd": "lock"})
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self.coordinator.api_post_all("/cmd", {"cmd": "unlock"})
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self):
        a = self.coordinator.data.get("admin", {})
        return {"locked_rooms": a.get("rooms_locked", 0), "total_rooms": a.get("rooms_total", 0)}


class AdminMaintenanceAllSwitch(CoordinatorEntity[SecureGateCoordinator], SwitchEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = "sg_admin_maintenance_all"
        self._attr_name = "SecureGate Alle Wartung"
        self._attr_icon = "mdi:wrench-clock"

    @property
    def device_info(self):
        return _device_info_admin(self.coordinator)

    @property
    def is_on(self):
        return self.coordinator.data.get("admin", {}).get("rooms_maintenance", 0) > 0

    async def async_turn_on(self, **kwargs):
        await self.coordinator.api_post_all("/api/maintenance", {"action": "on", "duration": 0, "msg": "Via Home Assistant"})
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self.coordinator.api_post_all("/api/maintenance", {"action": "off"})
        await self.coordinator.async_request_refresh()
