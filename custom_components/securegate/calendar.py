"""Calendar platform for SecureGate v3 — Events."""
from __future__ import annotations
from datetime import datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN
from .coordinator import SecureGateCoordinator
from .helpers import device_admin


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SecureGateCalendar(coordinator)])


class SecureGateCalendar(CoordinatorEntity[SecureGateCoordinator], CalendarEntity):
    """SecureGate events as HA calendar."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = "sg_admin_calendar"
        self._attr_name = "SecureGate Events"
        self._attr_icon = "mdi:calendar-clock"

    @property
    def device_info(self):
        return device_admin(self.coordinator)

    @property
    def event(self) -> CalendarEvent | None:
        """Return next upcoming event."""
        events = self._parse_events()
        now = datetime.now()
        upcoming = [e for e in events if e.end > now]
        return upcoming[0] if upcoming else None

    async def async_get_events(self, hass, start_date: datetime, end_date: datetime) -> list[CalendarEvent]:
        """Return all events in the given range."""
        events = self._parse_events()
        return [e for e in events if e.start < end_date and e.end > start_date]

    def _parse_events(self) -> list[CalendarEvent]:
        """Parse SecureGate events to HA CalendarEvents."""
        raw = self.coordinator.data.get("events", [])
        events = []
        for ev in raw:
            try:
                title = ev.get("titel", ev.get("name", "Event"))
                ev_type = ev.get("typ", ev.get("type", ""))
                if ev_type:
                    title = f"[{ev_type.upper()}] {title}"

                start_str = ev.get("datum", ev.get("start", ""))
                if not start_str:
                    continue

                # Parse start
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"]:
                    try:
                        start = datetime.strptime(start_str, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    continue

                # Duration
                dur = int(ev.get("duration_min", ev.get("duration", 60)))
                end = start + timedelta(minutes=dur)

                desc_parts = []
                if ev.get("beschreibung"): desc_parts.append(ev["beschreibung"])
                if ev.get("raum"): desc_parts.append(f"Raum: {ev['raum']}")
                if ev.get("repeat_type"): desc_parts.append(f"Wiederholung: {ev['repeat_type']}")

                events.append(CalendarEvent(
                    start=start,
                    end=end,
                    summary=title,
                    description="\n".join(desc_parts) if desc_parts else None,
                ))
            except Exception:
                continue
        return sorted(events, key=lambda e: e.start)
