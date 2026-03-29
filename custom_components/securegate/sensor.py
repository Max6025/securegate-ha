"""Sensor platform for SecureGate v3."""
from __future__ import annotations
from homeassistant.components.sensor import SensorEntity, SensorStateClass, SensorDeviceClass
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
            RoomSensor(coordinator, p, n, "active_users", "mdi:account-group", "active_users", SensorStateClass.MEASUREMENT),
            RoomSensor(coordinator, p, n, "active_guests", "mdi:account-clock", "active_guests", SensorStateClass.MEASUREMENT),
            RoomSensor(coordinator, p, n, "today_logins", "mdi:login", "today_total", SensorStateClass.TOTAL_INCREASING),
            RoomStatusSensor(coordinator, p, n),
            RoomBroadcastSensor(coordinator, p, n),
            RoomAccentColorSensor(coordinator, p, n),
            RoomCountdownSensor(coordinator, p, n),
            RoomLastEventSensor(coordinator, p, n),
            RoomLastScanTagSensor(coordinator, p, n),
            RoomAccessTimeSensor(coordinator, p, n),
            RoomUptimeSensor(coordinator, p, n),
        ])
    entities.extend([
        AdminSensor(coordinator, "total_users", "mdi:account-group", "total_active_users", SensorStateClass.MEASUREMENT),
        AdminSensor(coordinator, "total_guests", "mdi:account-clock-outline", "total_active_guests", SensorStateClass.MEASUREMENT),
        AdminSensor(coordinator, "total_logins", "mdi:counter", "total_logins_today", SensorStateClass.TOTAL_INCREASING),
        AdminSensor(coordinator, "rooms_online", "mdi:access-point-check", "rooms_online", SensorStateClass.MEASUREMENT),
        AdminSensor(coordinator, "rooms_locked", "mdi:lock-alert", "rooms_locked", SensorStateClass.MEASUREMENT),
        AdminSensor(coordinator, "rooms_maintenance", "mdi:wrench", "rooms_maintenance", SensorStateClass.MEASUREMENT),
        AdminSystemHealth(coordinator),
        WeatherTempSensor(coordinator),
        WeatherConditionSensor(coordinator),
        StatAvgDuration(coordinator),
        StatBusiestHour(coordinator),
        StatPeakDay(coordinator),
    ])
    async_add_entities(entities)


# === ROOM SENSORS ===

class RoomSensor(CoordinatorEntity[SecureGateCoordinator], SensorEntity):
    def __init__(self, coordinator, port, room_name, key, icon, data_key, state_class=None):
        super().__init__(coordinator)
        self._port, self._room_name, self._data_key = port, room_name, data_key
        self._attr_unique_id = f"sg_{port}_{key}"
        self._attr_name = f"{room_name} {key.replace('_', ' ').title()}"
        self._attr_icon, self._attr_state_class = icon, state_class
    @property
    def device_info(self): return device_room(self.coordinator, self._port, self._room_name)
    @property
    def native_value(self): return self.coordinator.data.get("rooms", {}).get(self._port, {}).get(self._data_key, 0)
    @property
    def available(self): return self.coordinator.data.get("rooms", {}).get(self._port, {}).get("_online", False)


class RoomStatusSensor(CoordinatorEntity[SecureGateCoordinator], SensorEntity):
    def __init__(self, coordinator, port, room_name):
        super().__init__(coordinator)
        self._port, self._room_name = port, room_name
        self._attr_unique_id = f"sg_{port}_status"
        self._attr_name = f"{room_name} Status"
        self._attr_icon = "mdi:shield-check"
    @property
    def device_info(self): return device_room(self.coordinator, self._port, self._room_name)
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
        a = {"system_msg": r.get("system_msg", ""), "port": self._port, "online": r.get("_online", False)}
        if r.get("maintenance_mode"):
            a["maintenance_msg"] = r.get("maintenance_msg", "")
            a["maintenance_remain"] = round(r.get("maintenance_remain", 0))
        return a
    @property
    def available(self): return self.coordinator.data.get("rooms", {}).get(self._port, {}).get("_online", False)


class RoomBroadcastSensor(CoordinatorEntity[SecureGateCoordinator], SensorEntity):
    def __init__(self, coordinator, port, room_name):
        super().__init__(coordinator)
        self._port, self._room_name = port, room_name
        self._attr_unique_id = f"sg_{port}_broadcast"
        self._attr_name = f"{room_name} Broadcast"
        self._attr_icon = "mdi:bullhorn"
    @property
    def device_info(self): return device_room(self.coordinator, self._port, self._room_name)
    @property
    def native_value(self):
        r = self.coordinator.data.get("rooms", {}).get(self._port, {})
        return r.get("broadcast", "") or "—"
    @property
    def extra_state_attributes(self):
        r = self.coordinator.data.get("rooms", {}).get(self._port, {})
        return {"type": r.get("broadcast_type", ""), "remaining": round(r.get("bc_remain", 0))}
    @property
    def available(self): return self.coordinator.data.get("rooms", {}).get(self._port, {}).get("_online", False)


class RoomAccentColorSensor(CoordinatorEntity[SecureGateCoordinator], SensorEntity):
    def __init__(self, coordinator, port, room_name):
        super().__init__(coordinator)
        self._port, self._room_name = port, room_name
        self._attr_unique_id = f"sg_{port}_accent_color"
        self._attr_name = f"{room_name} Akzentfarbe"
        self._attr_icon = "mdi:palette"
    @property
    def device_info(self): return device_room(self.coordinator, self._port, self._room_name)
    @property
    def native_value(self): return self.coordinator.data.get("rooms", {}).get(self._port, {}).get("_config", {}).get("accent", "#c8a04a")
    @property
    def available(self): return self.coordinator.data.get("rooms", {}).get(self._port, {}).get("_online", False)


class RoomCountdownSensor(CoordinatorEntity[SecureGateCoordinator], SensorEntity):
    def __init__(self, coordinator, port, room_name):
        super().__init__(coordinator)
        self._port, self._room_name = port, room_name
        self._attr_unique_id = f"sg_{port}_countdown"
        self._attr_name = f"{room_name} Countdown"
        self._attr_icon = "mdi:timer"
    @property
    def device_info(self): return device_room(self.coordinator, self._port, self._room_name)
    @property
    def native_value(self):
        r = self.coordinator.data.get("rooms", {}).get(self._port, {})
        label, remain = r.get("countdown_label", ""), r.get("countdown_remain", 0)
        if label and remain > 0:
            m, s = divmod(int(remain), 60)
            return f"{label} ({m}:{s:02d})"
        return "—"
    @property
    def available(self): return self.coordinator.data.get("rooms", {}).get(self._port, {}).get("_online", False)


class RoomLastEventSensor(CoordinatorEntity[SecureGateCoordinator], SensorEntity):
    def __init__(self, coordinator, port, room_name):
        super().__init__(coordinator)
        self._port, self._room_name = port, room_name
        self._attr_unique_id = f"sg_{port}_last_event"
        self._attr_name = f"{room_name} Letztes Event"
        self._attr_icon = "mdi:card-account-details"
    @property
    def device_info(self): return device_room(self.coordinator, self._port, self._room_name)
    @property
    def native_value(self):
        ev = self.coordinator.data.get("rooms", {}).get(self._port, {}).get("event", {})
        return f"{ev.get('type', '')} {ev['name']}" if ev.get("name") else "—"
    @property
    def extra_state_attributes(self):
        ev = self.coordinator.data.get("rooms", {}).get(self._port, {}).get("event", {})
        return {k: v for k, v in ev.items() if v} if ev else {}
    @property
    def available(self): return self.coordinator.data.get("rooms", {}).get(self._port, {}).get("_online", False)


class RoomLastScanTagSensor(CoordinatorEntity[SecureGateCoordinator], SensorEntity):
    """Last scanned NFC tag ATR."""
    def __init__(self, coordinator, port, room_name):
        super().__init__(coordinator)
        self._port, self._room_name = port, room_name
        self._attr_unique_id = f"sg_{port}_last_tag"
        self._attr_name = f"{room_name} Letzter NFC-Tag"
        self._attr_icon = "mdi:nfc-variant"
    @property
    def device_info(self): return device_room(self.coordinator, self._port, self._room_name)
    @property
    def native_value(self):
        ev = self.coordinator.data.get("rooms", {}).get(self._port, {}).get("event", {})
        return ev.get("atr", "—") or "—"
    @property
    def extra_state_attributes(self):
        ev = self.coordinator.data.get("rooms", {}).get(self._port, {}).get("event", {})
        return {"name": ev.get("name", ""), "time": ev.get("time", ""), "known": bool(ev.get("name"))}
    @property
    def available(self): return self.coordinator.data.get("rooms", {}).get(self._port, {}).get("_online", False)


class RoomAccessTimeSensor(CoordinatorEntity[SecureGateCoordinator], SensorEntity):
    def __init__(self, coordinator, port, room_name):
        super().__init__(coordinator)
        self._port, self._room_name = port, room_name
        self._attr_unique_id = f"sg_{port}_access_time"
        self._attr_name = f"{room_name} Zugangszeiten"
        self._attr_icon = "mdi:clock-outline"
    @property
    def device_info(self): return device_room(self.coordinator, self._port, self._room_name)
    @property
    def native_value(self):
        cfg = self.coordinator.data.get("rooms", {}).get(self._port, {}).get("_config", {})
        if cfg.get("access_closed"): return f"Geschlossen ({cfg.get('access_reason', '')})"
        tf, tt = cfg.get("access_time_from", ""), cfg.get("access_time_to", "")
        return f"{tf} – {tt}" if tf and tt else "Unbegrenzt"
    @property
    def extra_state_attributes(self):
        cfg = self.coordinator.data.get("rooms", {}).get(self._port, {}).get("_config", {})
        a = {"closed": cfg.get("access_closed", False)}
        if cfg.get("access_time_from"): a["from"] = cfg["access_time_from"]
        if cfg.get("access_time_to"): a["to"] = cfg["access_time_to"]
        if cfg.get("access_lunch_enabled"): a["lunch"] = f"{cfg.get('access_lunch_from', '')} – {cfg.get('access_lunch_to', '')}"
        return a
    @property
    def available(self): return self.coordinator.data.get("rooms", {}).get(self._port, {}).get("_online", False)


class RoomUptimeSensor(CoordinatorEntity[SecureGateCoordinator], SensorEntity):
    def __init__(self, coordinator, port, room_name):
        super().__init__(coordinator)
        self._port, self._room_name = port, room_name
        self._attr_unique_id = f"sg_{port}_uptime"
        self._attr_name = f"{room_name} Uptime"
        self._attr_icon = "mdi:clock-check"
    @property
    def device_info(self): return device_room(self.coordinator, self._port, self._room_name)
    @property
    def native_value(self):
        up = self.coordinator.data.get("rooms", {}).get(self._port, {}).get("_config", {}).get("uptime", 0)
        if up > 0:
            h, m = int(up // 3600), int((up % 3600) // 60)
            return f"{h}h {m}m"
        return "—"
    @property
    def available(self): return self.coordinator.data.get("rooms", {}).get(self._port, {}).get("_online", False)


# === ADMIN SENSORS ===

class AdminSensor(CoordinatorEntity[SecureGateCoordinator], SensorEntity):
    def __init__(self, coordinator, key, icon, data_key, state_class=None):
        super().__init__(coordinator)
        self._data_key = data_key
        self._attr_unique_id = f"sg_admin_{key}"
        self._attr_name = f"SecureGate {key.replace('_', ' ').title()}"
        self._attr_icon, self._attr_state_class = icon, state_class
    @property
    def device_info(self): return device_admin(self.coordinator)
    @property
    def native_value(self): return self.coordinator.data.get("admin", {}).get(self._data_key, 0)


class AdminSystemHealth(CoordinatorEntity[SecureGateCoordinator], SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = "sg_admin_health"
        self._attr_name = "SecureGate System Health"
        self._attr_icon = "mdi:heart-pulse"
    @property
    def device_info(self): return device_admin(self.coordinator)
    @property
    def native_value(self):
        a = self.coordinator.data.get("admin", {})
        if a.get("rooms_online", 0) == 0: return "Offline"
        if a.get("rooms_maintenance", 0) > 0: return "Wartung"
        if a.get("rooms_locked", 0) > 0: return "Lockdown"
        if a.get("rooms_online", 0) < a.get("rooms_total", 0): return "Teilweise"
        return "OK"
    @property
    def extra_state_attributes(self):
        a = self.coordinator.data.get("admin", {})
        rooms = self.coordinator.data.get("rooms", {})
        rs = {}
        for port, data in rooms.items():
            n = data.get("_room_name", f"Port {port}")
            if not data.get("_online"): rs[n] = "Offline"
            elif data.get("maintenance_mode"): rs[n] = "Wartung"
            elif data.get("system_locked"): rs[n] = "Lockdown"
            else: rs[n] = "OK"
        return {**a, "rooms": rs}


# === WEATHER SENSORS ===

class WeatherTempSensor(CoordinatorEntity[SecureGateCoordinator], SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = "sg_admin_weather_temp"
        self._attr_name = "SecureGate Temperatur"
        self._attr_icon = "mdi:thermometer"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_native_unit_of_measurement = "°C"
    @property
    def device_info(self): return device_admin(self.coordinator)
    @property
    def native_value(self): return self.coordinator.data.get("weather", {}).get("temperature")
    @property
    def extra_state_attributes(self):
        w = self.coordinator.data.get("weather", {})
        return {k: v for k, v in w.items() if k != "temperature" and v is not None}


class WeatherConditionSensor(CoordinatorEntity[SecureGateCoordinator], SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = "sg_admin_weather_condition"
        self._attr_name = "SecureGate Wetter"
        self._attr_icon = "mdi:weather-partly-cloudy"
    @property
    def device_info(self): return device_admin(self.coordinator)
    @property
    def native_value(self):
        w = self.coordinator.data.get("weather", {})
        return w.get("condition", w.get("icon", "—"))
    @property
    def extra_state_attributes(self):
        w = self.coordinator.data.get("weather", {})
        return {"cloud_cover": w.get("cloud_cover"), "wind_speed": w.get("wind_speed"), "precipitation": w.get("precipitation")}


# === STATISTIC SENSORS ===

class StatAvgDuration(CoordinatorEntity[SecureGateCoordinator], SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = "sg_admin_stat_avg_duration"
        self._attr_name = "SecureGate Ø Anwesenheitszeit"
        self._attr_icon = "mdi:av-timer"
    @property
    def device_info(self): return device_admin(self.coordinator)
    @property
    def native_value(self):
        s = self.coordinator.data.get("statistics", {})
        m = s.get("avg_duration_min", 0)
        if m > 0:
            h, mi = divmod(int(m), 60)
            return f"{h}h {mi}m" if h else f"{mi}m"
        return "—"


class StatBusiestHour(CoordinatorEntity[SecureGateCoordinator], SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = "sg_admin_stat_busiest_hour"
        self._attr_name = "SecureGate Busiest Hour"
        self._attr_icon = "mdi:chart-bar"
    @property
    def device_info(self): return device_admin(self.coordinator)
    @property
    def native_value(self):
        s = self.coordinator.data.get("statistics", {})
        h = s.get("busiest_hour")
        return f"{h}:00" if h is not None else "—"
    @property
    def extra_state_attributes(self):
        return self.coordinator.data.get("statistics", {}).get("hourly", {})


class StatPeakDay(CoordinatorEntity[SecureGateCoordinator], SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = "sg_admin_stat_peak_day"
        self._attr_name = "SecureGate Peak Day"
        self._attr_icon = "mdi:calendar-star"
    @property
    def device_info(self): return device_admin(self.coordinator)
    @property
    def native_value(self):
        s = self.coordinator.data.get("statistics", {})
        return s.get("peak_day", "—")
    @property
    def extra_state_attributes(self):
        s = self.coordinator.data.get("statistics", {})
        return {"peak_count": s.get("peak_count", 0), "weekly": s.get("weekly", {})}
