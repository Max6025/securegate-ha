"""Sensor platform for SecureGate — Multi-Room."""
from __future__ import annotations
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, CONF_NAME, DEFAULT_NAME
from .coordinator import SecureGateCoordinator


def _device_info_room(coordinator, port, name):
    return {
        "identifiers": {(DOMAIN, f"{coordinator.host}:{port}")},
        "name": f"SecureGate — {name}",
        "manufacturer": "SecureGate",
        "model": "NFC Room Controller",
        "sw_version": "3.0",
        "via_device": (DOMAIN, f"{coordinator.host}_admin"),
    }

def _device_info_admin(coordinator):
    return {
        "identifiers": {(DOMAIN, f"{coordinator.host}_admin")},
        "name": "SecureGate Admin",
        "manufacturer": "SecureGate",
        "model": "Admin Panel",
        "sw_version": "3.0",
        "configuration_url": f"http://{coordinator.host}/admin/",
    }


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    rooms = entry.data.get("rooms", [])
    entities = []

    for room in rooms:
        p = room["port"]
        n = room["name"]
        # Per-Room Sensors
        entities.extend([
            RoomSensor(coordinator, p, n, "active_users", "mdi:account-group", "active_users", SensorStateClass.MEASUREMENT),
            RoomSensor(coordinator, p, n, "active_guests", "mdi:account-clock", "active_guests", SensorStateClass.MEASUREMENT),
            RoomSensor(coordinator, p, n, "today_logins", "mdi:login", "today_total", SensorStateClass.TOTAL_INCREASING),
            RoomStatusSensor(coordinator, p, n),
            RoomBroadcastSensor(coordinator, p, n),
            RoomAccentColorSensor(coordinator, p, n),
            RoomCountdownSensor(coordinator, p, n),
            RoomLastEventSensor(coordinator, p, n),
            RoomAccessTimeSensor(coordinator, p, n),
            RoomUptimeSensor(coordinator, p, n),
        ])

    # Admin Sensors
    entities.extend([
        AdminSensor(coordinator, "total_users", "mdi:account-group", "total_active_users", SensorStateClass.MEASUREMENT),
        AdminSensor(coordinator, "total_guests", "mdi:account-clock-outline", "total_active_guests", SensorStateClass.MEASUREMENT),
        AdminSensor(coordinator, "total_logins", "mdi:counter", "total_logins_today", SensorStateClass.TOTAL_INCREASING),
        AdminSensor(coordinator, "rooms_online", "mdi:access-point-check", "rooms_online", SensorStateClass.MEASUREMENT),
        AdminSensor(coordinator, "rooms_locked", "mdi:lock-alert", "rooms_locked", SensorStateClass.MEASUREMENT),
        AdminSensor(coordinator, "rooms_maintenance", "mdi:wrench", "rooms_maintenance", SensorStateClass.MEASUREMENT),
        AdminSystemHealth(coordinator),
    ])

    async_add_entities(entities)


class RoomSensor(CoordinatorEntity[SecureGateCoordinator], SensorEntity):
    """Generic room sensor."""
    def __init__(self, coordinator, port, room_name, key, icon, data_key, state_class=None):
        super().__init__(coordinator)
        self._port = port
        self._room_name = room_name
        self._data_key = data_key
        self._attr_unique_id = f"sg_{port}_{key}"
        self._attr_name = f"{room_name} {key.replace('_', ' ').title()}"
        self._attr_icon = icon
        self._attr_state_class = state_class

    @property
    def device_info(self):
        return _device_info_room(self.coordinator, self._port, self._room_name)

    @property
    def native_value(self):
        room = self.coordinator.data.get("rooms", {}).get(self._port, {})
        return room.get(self._data_key, 0)

    @property
    def available(self):
        return self.coordinator.data.get("rooms", {}).get(self._port, {}).get("_online", False)


class RoomStatusSensor(CoordinatorEntity[SecureGateCoordinator], SensorEntity):
    """Room system status."""
    def __init__(self, coordinator, port, room_name):
        super().__init__(coordinator)
        self._port = port
        self._room_name = room_name
        self._attr_unique_id = f"sg_{port}_status"
        self._attr_name = f"{room_name} Status"
        self._attr_icon = "mdi:shield-check"

    @property
    def device_info(self):
        return _device_info_room(self.coordinator, self._port, self._room_name)

    @property
    def native_value(self):
        r = self.coordinator.data.get("rooms", {}).get(self._port, {})
        if not r.get("_online"): return "Offline"
        if r.get("maintenance_mode"): return "Wartungsmodus"
        if r.get("system_locked"): return "Lockdown"
        if r.get("master_mode"): return "Master-Modus"
        return "Bereit"

    @property
    def extra_state_attributes(self):
        r = self.coordinator.data.get("rooms", {}).get(self._port, {})
        attrs = {"system_msg": r.get("system_msg", ""), "port": self._port, "online": r.get("_online", False)}
        if r.get("maintenance_mode"):
            attrs["maintenance_msg"] = r.get("maintenance_msg", "")
            attrs["maintenance_remain"] = round(r.get("maintenance_remain", 0))
        return attrs

    @property
    def available(self):
        return self.coordinator.data.get("rooms", {}).get(self._port, {}).get("_online", False)


class RoomBroadcastSensor(CoordinatorEntity[SecureGateCoordinator], SensorEntity):
    """Current broadcast."""
    def __init__(self, coordinator, port, room_name):
        super().__init__(coordinator)
        self._port = port
        self._room_name = room_name
        self._attr_unique_id = f"sg_{port}_broadcast"
        self._attr_name = f"{room_name} Broadcast"
        self._attr_icon = "mdi:bullhorn"

    @property
    def device_info(self):
        return _device_info_room(self.coordinator, self._port, self._room_name)

    @property
    def native_value(self):
        r = self.coordinator.data.get("rooms", {}).get(self._port, {})
        return r.get("broadcast", "") or "—"

    @property
    def extra_state_attributes(self):
        r = self.coordinator.data.get("rooms", {}).get(self._port, {})
        return {"type": r.get("broadcast_type", ""), "remaining": round(r.get("bc_remain", 0)), "total": r.get("bc_total", 0)}

    @property
    def available(self):
        return self.coordinator.data.get("rooms", {}).get(self._port, {}).get("_online", False)


class RoomAccentColorSensor(CoordinatorEntity[SecureGateCoordinator], SensorEntity):
    """Current accent color."""
    def __init__(self, coordinator, port, room_name):
        super().__init__(coordinator)
        self._port = port
        self._room_name = room_name
        self._attr_unique_id = f"sg_{port}_accent_color"
        self._attr_name = f"{room_name} Akzentfarbe"
        self._attr_icon = "mdi:palette"

    @property
    def device_info(self):
        return _device_info_room(self.coordinator, self._port, self._room_name)

    @property
    def native_value(self):
        r = self.coordinator.data.get("rooms", {}).get(self._port, {})
        cfg = r.get("_config", {})
        return cfg.get("accent", "#c8a04a")

    @property
    def extra_state_attributes(self):
        r = self.coordinator.data.get("rooms", {}).get(self._port, {})
        cfg = r.get("_config", {})
        return {"dynamic": cfg.get("accent_dynamic", False), "room_name": cfg.get("room_name", "")}

    @property
    def available(self):
        return self.coordinator.data.get("rooms", {}).get(self._port, {}).get("_online", False)


class RoomCountdownSensor(CoordinatorEntity[SecureGateCoordinator], SensorEntity):
    """Active countdown timer."""
    def __init__(self, coordinator, port, room_name):
        super().__init__(coordinator)
        self._port = port
        self._room_name = room_name
        self._attr_unique_id = f"sg_{port}_countdown"
        self._attr_name = f"{room_name} Countdown"
        self._attr_icon = "mdi:timer"

    @property
    def device_info(self):
        return _device_info_room(self.coordinator, self._port, self._room_name)

    @property
    def native_value(self):
        r = self.coordinator.data.get("rooms", {}).get(self._port, {})
        label = r.get("countdown_label", "")
        remain = r.get("countdown_remain", 0)
        if label and remain > 0:
            m, s = divmod(int(remain), 60)
            return f"{label} ({m}:{s:02d})"
        return "—"

    @property
    def available(self):
        return self.coordinator.data.get("rooms", {}).get(self._port, {}).get("_online", False)


class RoomLastEventSensor(CoordinatorEntity[SecureGateCoordinator], SensorEntity):
    """Last scan event."""
    def __init__(self, coordinator, port, room_name):
        super().__init__(coordinator)
        self._port = port
        self._room_name = room_name
        self._attr_unique_id = f"sg_{port}_last_event"
        self._attr_name = f"{room_name} Letztes Event"
        self._attr_icon = "mdi:card-account-details"

    @property
    def device_info(self):
        return _device_info_room(self.coordinator, self._port, self._room_name)

    @property
    def native_value(self):
        r = self.coordinator.data.get("rooms", {}).get(self._port, {})
        ev = r.get("event", {})
        if ev and ev.get("name"):
            return f"{ev.get('type', '')} {ev['name']}"
        return "—"

    @property
    def extra_state_attributes(self):
        r = self.coordinator.data.get("rooms", {}).get(self._port, {})
        ev = r.get("event", {})
        if ev:
            return {k: v for k, v in ev.items() if v}
        return {}

    @property
    def available(self):
        return self.coordinator.data.get("rooms", {}).get(self._port, {}).get("_online", False)


class RoomAccessTimeSensor(CoordinatorEntity[SecureGateCoordinator], SensorEntity):
    """Access time window."""
    def __init__(self, coordinator, port, room_name):
        super().__init__(coordinator)
        self._port = port
        self._room_name = room_name
        self._attr_unique_id = f"sg_{port}_access_time"
        self._attr_name = f"{room_name} Zugangszeiten"
        self._attr_icon = "mdi:clock-outline"

    @property
    def device_info(self):
        return _device_info_room(self.coordinator, self._port, self._room_name)

    @property
    def native_value(self):
        r = self.coordinator.data.get("rooms", {}).get(self._port, {})
        cfg = r.get("_config", {})
        if cfg.get("access_closed"):
            return f"Geschlossen ({cfg.get('access_reason', '')})"
        tf = cfg.get("access_time_from", "")
        tt = cfg.get("access_time_to", "")
        if tf and tt:
            return f"{tf} – {tt}"
        return "Unbegrenzt"

    @property
    def extra_state_attributes(self):
        r = self.coordinator.data.get("rooms", {}).get(self._port, {})
        cfg = r.get("_config", {})
        attrs = {}
        if cfg.get("access_time_from"): attrs["from"] = cfg["access_time_from"]
        if cfg.get("access_time_to"): attrs["to"] = cfg["access_time_to"]
        attrs["closed"] = cfg.get("access_closed", False)
        attrs["override_active"] = cfg.get("override_remain", 0) > 0
        if cfg.get("access_lunch_enabled"):
            attrs["lunch"] = f"{cfg.get('access_lunch_from', '')} – {cfg.get('access_lunch_to', '')}"
        return attrs

    @property
    def available(self):
        return self.coordinator.data.get("rooms", {}).get(self._port, {}).get("_online", False)


class RoomUptimeSensor(CoordinatorEntity[SecureGateCoordinator], SensorEntity):
    """Room uptime."""
    def __init__(self, coordinator, port, room_name):
        super().__init__(coordinator)
        self._port = port
        self._room_name = room_name
        self._attr_unique_id = f"sg_{port}_uptime"
        self._attr_name = f"{room_name} Uptime"
        self._attr_icon = "mdi:clock-check"

    @property
    def device_info(self):
        return _device_info_room(self.coordinator, self._port, self._room_name)

    @property
    def native_value(self):
        r = self.coordinator.data.get("rooms", {}).get(self._port, {})
        cfg = r.get("_config", {})
        up = cfg.get("uptime", 0)
        if up > 0:
            h = int(up // 3600)
            m = int((up % 3600) // 60)
            return f"{h}h {m}m"
        return "—"

    @property
    def available(self):
        return self.coordinator.data.get("rooms", {}).get(self._port, {}).get("_online", False)


# === ADMIN SENSORS ===

class AdminSensor(CoordinatorEntity[SecureGateCoordinator], SensorEntity):
    """Admin aggregate sensor."""
    def __init__(self, coordinator, key, icon, data_key, state_class=None):
        super().__init__(coordinator)
        self._data_key = data_key
        self._attr_unique_id = f"sg_admin_{key}"
        self._attr_name = f"SecureGate {key.replace('_', ' ').title()}"
        self._attr_icon = icon
        self._attr_state_class = state_class

    @property
    def device_info(self):
        return _device_info_admin(self.coordinator)

    @property
    def native_value(self):
        return self.coordinator.data.get("admin", {}).get(self._data_key, 0)


class AdminSystemHealth(CoordinatorEntity[SecureGateCoordinator], SensorEntity):
    """Overall system health."""
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = "sg_admin_health"
        self._attr_name = "SecureGate System Health"
        self._attr_icon = "mdi:heart-pulse"

    @property
    def device_info(self):
        return _device_info_admin(self.coordinator)

    @property
    def native_value(self):
        admin = self.coordinator.data.get("admin", {})
        online = admin.get("rooms_online", 0)
        total = admin.get("rooms_total", 0)
        locked = admin.get("rooms_locked", 0)
        maint = admin.get("rooms_maintenance", 0)
        if online == 0: return "Offline"
        if maint > 0: return "Wartung"
        if locked > 0: return "Lockdown"
        if online < total: return "Teilweise"
        return "OK"

    @property
    def extra_state_attributes(self):
        admin = self.coordinator.data.get("admin", {})
        rooms = self.coordinator.data.get("rooms", {})
        room_status = {}
        for port, data in rooms.items():
            name = data.get("_room_name", f"Port {port}")
            if not data.get("_online"): room_status[name] = "Offline"
            elif data.get("maintenance_mode"): room_status[name] = "Wartung"
            elif data.get("system_locked"): room_status[name] = "Lockdown"
            else: room_status[name] = "OK"
        return {**admin, "rooms": room_status}
