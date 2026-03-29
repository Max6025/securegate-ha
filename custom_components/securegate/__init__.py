"""SecureGate integration for Home Assistant — Multi-Room."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_HOST, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
from .coordinator import SecureGateCoordinator

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SecureGate from a config entry."""
    host = entry.data[CONF_HOST]
    rooms = entry.data.get("rooms", [{"name": "SecureGate", "port": 5000}])
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    coordinator = SecureGateCoordinator(hass, host, rooms, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Services
    async def handle_broadcast(call):
        msg = call.data.get("message", "")
        bc_type = call.data.get("type", "info")
        duration = call.data.get("duration", 300)
        port = call.data.get("port", 0)
        if port:
            await coordinator.api_post(port, "/cmd", {"cmd": f"bc {duration} {bc_type} {msg}"})
        else:
            await coordinator.api_post_all("/cmd", {"cmd": f"bc {duration} {bc_type} {msg}"})

    async def handle_kick_all(call):
        port = call.data.get("port", 0)
        if port:
            await coordinator.api_post(port, "/cmd", {"cmd": "kick all"})
        else:
            await coordinator.api_post_all("/cmd", {"cmd": "kick all"})

    async def handle_cmd(call):
        command = call.data.get("command", "")
        port = call.data.get("port", 0)
        if port:
            await coordinator.api_post(port, "/cmd", {"cmd": command})
        else:
            await coordinator.api_post_all("/cmd", {"cmd": command})

    async def handle_lockdown_all(call):
        await coordinator.api_post_all("/cmd", {"cmd": "lock"})

    async def handle_unlock_all(call):
        await coordinator.api_post_all("/cmd", {"cmd": "unlock"})

    async def handle_maintenance_all(call):
        duration = call.data.get("duration", 0)
        msg = call.data.get("message", "Wartungsmodus via Home Assistant")
        await coordinator.api_post_all("/api/maintenance", {"action": "on", "duration": duration, "msg": msg})

    async def handle_maintenance_off_all(call):
        await coordinator.api_post_all("/api/maintenance", {"action": "off"})

    if not hass.services.has_service(DOMAIN, "broadcast"):
        hass.services.async_register(DOMAIN, "broadcast", handle_broadcast)
        hass.services.async_register(DOMAIN, "kick_all", handle_kick_all)
        hass.services.async_register(DOMAIN, "cmd", handle_cmd)
        hass.services.async_register(DOMAIN, "lockdown_all", handle_lockdown_all)
        hass.services.async_register(DOMAIN, "unlock_all", handle_unlock_all)
        hass.services.async_register(DOMAIN, "maintenance_all", handle_maintenance_all)
        hass.services.async_register(DOMAIN, "maintenance_off_all", handle_maintenance_off_all)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
