"""Switch platform for SecureGate."""
from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_NAME, DEFAULT_NAME
from .coordinator import SecureGateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up switches."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    name = entry.data.get(CONF_NAME, DEFAULT_NAME)
    port = entry.data.get("port", 5000)

    async_add_entities([
        SecureGateLockdownSwitch(coordinator, entry, name, port),
        SecureGateMaintenanceSwitch(coordinator, entry, name, port),
    ])


class SecureGateSwitchBase(CoordinatorEntity[SecureGateCoordinator], SwitchEntity):
    """Base switch."""

    def __init__(self, coordinator, entry, name, port, key, icon):
        super().__init__(coordinator)
        self._attr_unique_id = f"securegate_{port}_{key}_switch"
        self._attr_name = f"{name} {key.replace('_', ' ').title()}"
        self._attr_icon = icon
        self._entry = entry

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"{self.coordinator.host}:{self.coordinator.port}")},
            "name": self._entry.data.get(CONF_NAME, DEFAULT_NAME),
            "manufacturer": "SecureGate",
            "model": "NFC Access Control",
        }


class SecureGateLockdownSwitch(SecureGateSwitchBase):
    """Lockdown switch."""

    def __init__(self, coordinator, entry, name, port):
        super().__init__(coordinator, entry, name, port, "lockdown", "mdi:lock-alert")

    @property
    def is_on(self):
        return self.coordinator.data.get("system_locked", False) and not self.coordinator.data.get("maintenance_mode", False)

    async def async_turn_on(self, **kwargs):
        """Activate lockdown."""
        await self.coordinator.api_post("/cmd", {"cmd": "lock"})
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Deactivate lockdown."""
        await self.coordinator.api_post("/cmd", {"cmd": "unlock"})
        await self.coordinator.async_request_refresh()


class SecureGateMaintenanceSwitch(SecureGateSwitchBase):
    """Maintenance mode switch."""

    def __init__(self, coordinator, entry, name, port):
        super().__init__(coordinator, entry, name, port, "maintenance", "mdi:wrench-cog")

    @property
    def is_on(self):
        return self.coordinator.data.get("maintenance_mode", False)

    async def async_turn_on(self, **kwargs):
        """Activate maintenance."""
        await self.coordinator.api_post("/api/maintenance", {"action": "on", "duration": 0, "msg": "Wartungsmodus via Home Assistant"})
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Deactivate maintenance."""
        await self.coordinator.api_post("/api/maintenance", {"action": "off"})
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self):
        d = self.coordinator.data
        if d.get("maintenance_mode"):
            return {
                "message": d.get("maintenance_msg", ""),
                "remaining": d.get("maintenance_remain", 0),
            }
        return {}
