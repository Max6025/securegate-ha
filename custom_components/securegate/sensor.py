"""Sensor platform for SecureGate."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_NAME, DEFAULT_NAME
from .coordinator import SecureGateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    name = entry.data.get(CONF_NAME, DEFAULT_NAME)
    port = entry.data.get("port", 5000)

    async_add_entities([
        SecureGateActiveUsers(coordinator, entry, name, port),
        SecureGateActiveGuests(coordinator, entry, name, port),
        SecureGateTodayLogins(coordinator, entry, name, port),
        SecureGateStatus(coordinator, entry, name, port),
        SecureGateBroadcast(coordinator, entry, name, port),
    ])


class SecureGateBase(CoordinatorEntity[SecureGateCoordinator], SensorEntity):
    """Base class for SecureGate sensors."""

    def __init__(self, coordinator, entry, name, port, key, icon, unit=None):
        super().__init__(coordinator)
        self._attr_unique_id = f"securegate_{port}_{key}"
        self._attr_name = f"{name} {key.replace('_', ' ').title()}"
        self._attr_icon = icon
        self._attr_native_unit_of_measurement = unit
        self._entry = entry
        self._key = key

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"{self.coordinator.host}:{self.coordinator.port}")},
            "name": self._entry.data.get(CONF_NAME, DEFAULT_NAME),
            "manufacturer": "SecureGate",
            "model": "NFC Access Control",
            "sw_version": "3.0",
            "configuration_url": f"http://{self.coordinator.host}/admin/",
        }


class SecureGateActiveUsers(SecureGateBase):
    """Active users sensor."""

    def __init__(self, coordinator, entry, name, port):
        super().__init__(coordinator, entry, name, port, "active_users", "mdi:account-group")
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        return self.coordinator.data.get("active_users", 0)

    @property
    def extra_state_attributes(self):
        users = self.coordinator.data.get("users", [])
        return {
            "users": [f"{u.get('vorname', '')} {u.get('nachname', '')}" for u in users if u.get("status") == "active"],
            "count": self.coordinator.data.get("active_users", 0),
        }


class SecureGateActiveGuests(SecureGateBase):
    """Active guests sensor."""

    def __init__(self, coordinator, entry, name, port):
        super().__init__(coordinator, entry, name, port, "active_guests", "mdi:account-clock")
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        return self.coordinator.data.get("active_guests", 0)


class SecureGateTodayLogins(SecureGateBase):
    """Today's total logins sensor."""

    def __init__(self, coordinator, entry, name, port):
        super().__init__(coordinator, entry, name, port, "today_logins", "mdi:login")
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self):
        return self.coordinator.data.get("today_total", 0)


class SecureGateStatus(SecureGateBase):
    """System status sensor."""

    def __init__(self, coordinator, entry, name, port):
        super().__init__(coordinator, entry, name, port, "status", "mdi:shield-check")

    @property
    def native_value(self):
        d = self.coordinator.data
        if d.get("maintenance_mode"):
            return "Wartungsmodus"
        if d.get("system_locked"):
            return "Lockdown"
        return "Bereit"

    @property
    def extra_state_attributes(self):
        d = self.coordinator.data
        attrs = {"system_msg": d.get("system_msg", "")}
        if d.get("maintenance_mode"):
            attrs["maintenance_msg"] = d.get("maintenance_msg", "")
            attrs["maintenance_remain"] = d.get("maintenance_remain", 0)
        if d.get("countdown_label"):
            attrs["countdown"] = d.get("countdown_label", "")
            attrs["countdown_remain"] = d.get("countdown_remain", 0)
        return attrs


class SecureGateBroadcast(SecureGateBase):
    """Current broadcast sensor."""

    def __init__(self, coordinator, entry, name, port):
        super().__init__(coordinator, entry, name, port, "broadcast", "mdi:bullhorn")

    @property
    def native_value(self):
        return self.coordinator.data.get("broadcast", "") or "Kein Broadcast"

    @property
    def extra_state_attributes(self):
        d = self.coordinator.data
        return {
            "type": d.get("broadcast_type", ""),
            "remaining": d.get("bc_remain", 0),
        }
