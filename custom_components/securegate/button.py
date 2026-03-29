"""Button platform for SecureGate v3."""
from __future__ import annotations
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN
from .coordinator import SecureGateCoordinator
from .helpers import device_room, device_admin


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    rooms = entry.data.get("rooms", [])
    entities = []
    for room in rooms:
        p, n = room["port"], room["name"]
        entities.extend([
            RoomKickAll(coordinator, p, n),
            RoomRestart(coordinator, p, n),
        ])
    entities.extend([
        AdminKickAll(coordinator),
        AdminLockdownAll(coordinator),
        AdminUnlockAll(coordinator),
        AdminBackup(coordinator),
    ])
    async_add_entities(entities)


class RoomKickAll(CoordinatorEntity[SecureGateCoordinator], ButtonEntity):
    def __init__(self, coordinator, port, room_name):
        super().__init__(coordinator)
        self._port, self._room_name = port, room_name
        self._attr_unique_id = f"sg_{port}_kick_all"
        self._attr_name = f"{room_name} Alle Auschecken"
        self._attr_icon = "mdi:account-arrow-right"
    @property
    def device_info(self): return device_room(self.coordinator, self._port, self._room_name)
    async def async_press(self):
        await self.coordinator.api_post(self._port, "/cmd", {"cmd": "kick all"})
        await self.coordinator.async_request_refresh()
    @property
    def available(self): return self.coordinator.data.get("rooms", {}).get(self._port, {}).get("_online", False)


class RoomRestart(CoordinatorEntity[SecureGateCoordinator], ButtonEntity):
    def __init__(self, coordinator, port, room_name):
        super().__init__(coordinator)
        self._port, self._room_name = port, room_name
        self._attr_unique_id = f"sg_{port}_restart"
        self._attr_name = f"{room_name} Neustart"
        self._attr_icon = "mdi:restart"
    @property
    def device_info(self): return device_room(self.coordinator, self._port, self._room_name)
    async def async_press(self):
        await self.coordinator.api_post(self._port, "/cmd", {"cmd": "restart"})
    @property
    def available(self): return self.coordinator.data.get("rooms", {}).get(self._port, {}).get("_online", False)


class AdminKickAll(CoordinatorEntity[SecureGateCoordinator], ButtonEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = "sg_admin_kick_all"
        self._attr_name = "SecureGate Alle Auschecken"
        self._attr_icon = "mdi:account-arrow-right-outline"
    @property
    def device_info(self): return device_admin(self.coordinator)
    async def async_press(self):
        await self.coordinator.api_post_all("/cmd", {"cmd": "kick all"})
        await self.coordinator.async_request_refresh()


class AdminLockdownAll(CoordinatorEntity[SecureGateCoordinator], ButtonEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = "sg_admin_lockdown_all_btn"
        self._attr_name = "SecureGate Alle Sperren"
        self._attr_icon = "mdi:lock"
    @property
    def device_info(self): return device_admin(self.coordinator)
    async def async_press(self):
        await self.coordinator.api_post_all("/cmd", {"cmd": "lock"})
        await self.coordinator.async_request_refresh()


class AdminUnlockAll(CoordinatorEntity[SecureGateCoordinator], ButtonEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = "sg_admin_unlock_all_btn"
        self._attr_name = "SecureGate Alle Entsperren"
        self._attr_icon = "mdi:lock-open"
    @property
    def device_info(self): return device_admin(self.coordinator)
    async def async_press(self):
        await self.coordinator.api_post_all("/cmd", {"cmd": "unlock"})
        await self.coordinator.async_request_refresh()


class AdminBackup(CoordinatorEntity[SecureGateCoordinator], ButtonEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = "sg_admin_backup"
        self._attr_name = "SecureGate Backup Erstellen"
        self._attr_icon = "mdi:database-export"
    @property
    def device_info(self): return device_admin(self.coordinator)
    async def async_press(self):
        await self.coordinator.api_post(self.coordinator.rooms[0]["port"], "/cmd", {"cmd": "backup"})
