"""Select platform for SecureGate v3 — Broadcast type."""
from __future__ import annotations
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN
from .coordinator import SecureGateCoordinator
from .helpers import device_admin


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([BroadcastTypeSelect(coordinator)])


class BroadcastTypeSelect(CoordinatorEntity[SecureGateCoordinator], SelectEntity):
    """Select broadcast type."""
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = "sg_admin_broadcast_type"
        self._attr_name = "SecureGate Broadcast Typ"
        self._attr_icon = "mdi:format-list-bulleted-type"
        self._attr_options = ["info", "warnung", "erfolg", "alarm"]
        self._attr_current_option = "info"

    @property
    def device_info(self): return device_admin(self.coordinator)

    async def async_select_option(self, option: str) -> None:
        self._attr_current_option = option
        self.async_write_ha_state()
