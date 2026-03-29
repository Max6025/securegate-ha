"""Binary sensor platform for SecureGate."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_NAME, DEFAULT_NAME
from .coordinator import SecureGateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up binary sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    name = entry.data.get(CONF_NAME, DEFAULT_NAME)
    port = entry.data.get("port", 5000)

    async_add_entities([
        SecureGateLocked(coordinator, entry, name, port),
        SecureGateMaintenance(coordinator, entry, name, port),
        SecureGateCardStuck(coordinator, entry, name, port),
        SecureGateReaderError(coordinator, entry, name, port),
    ])


class SecureGateBinaryBase(CoordinatorEntity[SecureGateCoordinator], BinarySensorEntity):
    """Base binary sensor."""

    def __init__(self, coordinator, entry, name, port, key, icon, device_class=None):
        super().__init__(coordinator)
        self._attr_unique_id = f"securegate_{port}_{key}"
        self._attr_name = f"{name} {key.replace('_', ' ').title()}"
        self._attr_icon = icon
        self._attr_device_class = device_class
        self._entry = entry

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"{self.coordinator.host}:{self.coordinator.port}")},
            "name": self._entry.data.get(CONF_NAME, DEFAULT_NAME),
            "manufacturer": "SecureGate",
            "model": "NFC Access Control",
        }


class SecureGateLocked(SecureGateBinaryBase):
    """System locked binary sensor."""

    def __init__(self, coordinator, entry, name, port):
        super().__init__(coordinator, entry, name, port, "locked", "mdi:lock", BinarySensorDeviceClass.LOCK)

    @property
    def is_on(self):
        return self.coordinator.data.get("system_locked", False)


class SecureGateMaintenance(SecureGateBinaryBase):
    """Maintenance mode binary sensor."""

    def __init__(self, coordinator, entry, name, port):
        super().__init__(coordinator, entry, name, port, "maintenance", "mdi:wrench")

    @property
    def is_on(self):
        return self.coordinator.data.get("maintenance_mode", False)

    @property
    def extra_state_attributes(self):
        d = self.coordinator.data
        if d.get("maintenance_mode"):
            return {
                "message": d.get("maintenance_msg", ""),
                "remaining_seconds": d.get("maintenance_remain", 0),
            }
        return {}


class SecureGateCardStuck(SecureGateBinaryBase):
    """Card stuck warning."""

    def __init__(self, coordinator, entry, name, port):
        super().__init__(coordinator, entry, name, port, "card_stuck", "mdi:credit-card-alert", BinarySensorDeviceClass.PROBLEM)

    @property
    def is_on(self):
        return self.coordinator.data.get("card_stuck", False)


class SecureGateReaderError(SecureGateBinaryBase):
    """Reader error."""

    def __init__(self, coordinator, entry, name, port):
        super().__init__(coordinator, entry, name, port, "reader_error", "mdi:alert-circle", BinarySensorDeviceClass.PROBLEM)

    @property
    def is_on(self):
        return self.coordinator.data.get("reader_error", False)
