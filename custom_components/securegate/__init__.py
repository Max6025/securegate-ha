"""SecureGate integration for Home Assistant."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL, DEFAULT_PORT, DEFAULT_SCAN_INTERVAL
from .coordinator import SecureGateCoordinator

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SecureGate from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    coordinator = SecureGateCoordinator(hass, host, port, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Register services
    async def handle_broadcast(call):
        msg = call.data.get("message", "")
        bc_type = call.data.get("type", "info")
        duration = call.data.get("duration", 300)
        await coordinator.api_post("/cmd", {"cmd": f"bc {duration} {bc_type} {msg}"})

    async def handle_kick_all(call):
        await coordinator.api_post("/cmd", {"cmd": "kick all"})

    async def handle_cmd(call):
        command = call.data.get("command", "")
        await coordinator.api_post("/cmd", {"cmd": command})

    if not hass.services.has_service(DOMAIN, "broadcast"):
        hass.services.async_register(DOMAIN, "broadcast", handle_broadcast)
        hass.services.async_register(DOMAIN, "kick_all", handle_kick_all)
        hass.services.async_register(DOMAIN, "cmd", handle_cmd)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
