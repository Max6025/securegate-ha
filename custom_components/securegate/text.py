"""Text platform for SecureGate v3 — Broadcast input."""
from __future__ import annotations
from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN
from .coordinator import SecureGateCoordinator
from .helpers import device_admin


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([BroadcastText(coordinator)])


class BroadcastText(CoordinatorEntity[SecureGateCoordinator], TextEntity):
    """Text input for broadcast message."""
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = "sg_admin_broadcast_text"
        self._attr_name = "SecureGate Broadcast Text"
        self._attr_icon = "mdi:message-text"
        self._attr_native_max = 200
        self._value = ""

    @property
    def device_info(self): return device_admin(self.coordinator)

    @property
    def native_value(self): return self._value

    async def async_set_value(self, value: str) -> None:
        self._value = value
        if value.strip():
            await self.coordinator.api_post_all("/cmd", {"cmd": f"bc 300 info {value}"})
            await self.coordinator.async_request_refresh()
