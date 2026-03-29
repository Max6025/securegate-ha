"""Binary sensors for SecureGate — Multi-Room."""
from __future__ import annotations
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN
from .coordinator import SecureGateCoordinator
from .sensor import _device_info_room, _device_info_admin


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    rooms = entry.data.get("rooms", [])
    entities = []
    for room in rooms:
        p, n = room["port"], room["name"]
        entities.extend([
            RoomBinary(coordinator, p, n, "locked", "mdi:lock", "system_locked", BinarySensorDeviceClass.LOCK),
            RoomBinary(coordinator, p, n, "maintenance", "mdi:wrench", "maintenance_mode"),
            RoomBinary(coordinator, p, n, "master_mode", "mdi:star", "master_mode"),
            RoomBinary(coordinator, p, n, "card_stuck", "mdi:credit-card-alert", "card_stuck", BinarySensorDeviceClass.PROBLEM),
            RoomBinary(coordinator, p, n, "reader_error", "mdi:alert-circle", "reader_error", BinarySensorDeviceClass.PROBLEM),
            RoomBinary(coordinator, p, n, "invalid_card", "mdi:credit-card-off", "invalid_card_active", BinarySensorDeviceClass.PROBLEM),
            RoomOnlineBinary(coordinator, p, n),
            RoomAccessClosedBinary(coordinator, p, n),
        ])
    # Admin
    entities.append(AdminAllOnline(coordinator, rooms))
    entities.append(AdminAnyLocked(coordinator))
    entities.append(AdminAnyMaintenance(coordinator))
    async_add_entities(entities)


class RoomBinary(CoordinatorEntity[SecureGateCoordinator], BinarySensorEntity):
    def __init__(self, coordinator, port, room_name, key, icon, data_key, device_class=None):
        super().__init__(coordinator)
        self._port = port
        self._room_name = room_name
        self._data_key = data_key
        self._attr_unique_id = f"sg_{port}_{key}"
        self._attr_name = f"{room_name} {key.replace('_', ' ').title()}"
        self._attr_icon = icon
        self._attr_device_class = device_class

    @property
    def device_info(self):
        return _device_info_room(self.coordinator, self._port, self._room_name)

    @property
    def is_on(self):
        return self.coordinator.data.get("rooms", {}).get(self._port, {}).get(self._data_key, False)

    @property
    def available(self):
        return self.coordinator.data.get("rooms", {}).get(self._port, {}).get("_online", False)


class RoomOnlineBinary(CoordinatorEntity[SecureGateCoordinator], BinarySensorEntity):
    def __init__(self, coordinator, port, room_name):
        super().__init__(coordinator)
        self._port = port
        self._room_name = room_name
        self._attr_unique_id = f"sg_{port}_online"
        self._attr_name = f"{room_name} Online"
        self._attr_icon = "mdi:access-point-check"
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    @property
    def device_info(self):
        return _device_info_room(self.coordinator, self._port, self._room_name)

    @property
    def is_on(self):
        return self.coordinator.data.get("rooms", {}).get(self._port, {}).get("_online", False)


class RoomAccessClosedBinary(CoordinatorEntity[SecureGateCoordinator], BinarySensorEntity):
    def __init__(self, coordinator, port, room_name):
        super().__init__(coordinator)
        self._port = port
        self._room_name = room_name
        self._attr_unique_id = f"sg_{port}_access_closed"
        self._attr_name = f"{room_name} Zugang Geschlossen"
        self._attr_icon = "mdi:door-closed-lock"

    @property
    def device_info(self):
        return _device_info_room(self.coordinator, self._port, self._room_name)

    @property
    def is_on(self):
        r = self.coordinator.data.get("rooms", {}).get(self._port, {})
        return r.get("_config", {}).get("access_closed", False)

    @property
    def extra_state_attributes(self):
        r = self.coordinator.data.get("rooms", {}).get(self._port, {})
        cfg = r.get("_config", {})
        return {"reason": cfg.get("access_reason", "")}

    @property
    def available(self):
        return self.coordinator.data.get("rooms", {}).get(self._port, {}).get("_online", False)


# Admin binary sensors
class AdminAllOnline(CoordinatorEntity[SecureGateCoordinator], BinarySensorEntity):
    def __init__(self, coordinator, rooms):
        super().__init__(coordinator)
        self._rooms = rooms
        self._attr_unique_id = "sg_admin_all_online"
        self._attr_name = "SecureGate Alle Online"
        self._attr_icon = "mdi:check-network"
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    @property
    def device_info(self):
        return _device_info_admin(self.coordinator)

    @property
    def is_on(self):
        a = self.coordinator.data.get("admin", {})
        return a.get("rooms_online", 0) == a.get("rooms_total", 0) and a.get("rooms_total", 0) > 0


class AdminAnyLocked(CoordinatorEntity[SecureGateCoordinator], BinarySensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = "sg_admin_any_locked"
        self._attr_name = "SecureGate Lockdown Aktiv"
        self._attr_icon = "mdi:lock-alert"

    @property
    def device_info(self):
        return _device_info_admin(self.coordinator)

    @property
    def is_on(self):
        return self.coordinator.data.get("admin", {}).get("rooms_locked", 0) > 0


class AdminAnyMaintenance(CoordinatorEntity[SecureGateCoordinator], BinarySensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = "sg_admin_any_maintenance"
        self._attr_name = "SecureGate Wartung Aktiv"
        self._attr_icon = "mdi:wrench-cog"

    @property
    def device_info(self):
        return _device_info_admin(self.coordinator)

    @property
    def is_on(self):
        return self.coordinator.data.get("admin", {}).get("rooms_maintenance", 0) > 0
